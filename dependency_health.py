"""
Dependency Health Check - Monitor package health and vulnerabilities
Phase 1 Feature: Dependency Analysis
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import concurrent.futures

class DependencyHealthCheck:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.report_dir = self.base_dir / 'dependency-reports'
        self.report_dir.mkdir(exist_ok=True)
        
        self.requirements_file = self.base_dir / 'BitBucket' / 'requirements.txt'
        self.packages = self._parse_requirements()
        
        self.pypi_cache = self.report_dir / 'pypi_cache.json'
        self.vuln_cache = self.report_dir / 'vuln_cache.json'
        self._load_caches()
    
    def _load_caches(self):
        """Load cached data"""
        self.pypi_data = {}
        self.vuln_data = {}
        
        if self.pypi_cache.exists():
            with open(self.pypi_cache, 'r', encoding='utf-8') as f:
                self.pypi_data = json.load(f)
        
        if self.vuln_cache.exists():
            with open(self.vuln_cache, 'r', encoding='utf-8') as f:
                self.vuln_data = json.load(f)
    
    def _save_caches(self):
        """Save cached data"""
        with open(self.pypi_cache, 'w', encoding='utf-8') as f:
            json.dump(self.pypi_data, f, indent=2)
        
        with open(self.vuln_cache, 'w', encoding='utf-8') as f:
            json.dump(self.vuln_data, f, indent=2)
    
    def _parse_requirements(self) -> List[Dict[str, str]]:
        """Parse requirements.txt file"""
        packages = []
        
        if not self.requirements_file.exists():
            print(f"[WARN] Requirements file not found: {self.requirements_file}")
            return packages
        
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '==' in line:
                    name, version = line.split('==', 1)
                    packages.append({
                        'name': name.strip(),
                        'version': version.strip(),
                        'specifier': '=='
                    })
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                    packages.append({
                        'name': name.strip(),
                        'version': version.strip(),
                        'specifier': '>='
                    })
                elif '<=' in line:
                    name, version = line.split('<=', 1)
                    packages.append({
                        'name': name.strip(),
                        'version': version.strip(),
                        'specifier': '<='
                    })
                else:
                    packages.append({
                        'name': line.strip(),
                        'version': None,
                        'specifier': None
                    })
        
        return packages
    
    def get_package_info(self, package_name: str) -> Dict:
        """Get package info from PyPI"""
        if package_name in self.pypi_data:
            cached = self.pypi_data[package_name]
            cached_time = datetime.fromisoformat(cached['cached_at'])
            
            if datetime.now() - cached_time < timedelta(hours=24):
                return cached['data']
        
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.pypi_data[package_name] = {
                    'cached_at': datetime.now().isoformat(),
                    'data': data
                }
                
                return data
            
        except Exception as e:
            print(f"[WARN] Error fetching {package_name}: {e}")
        
        return {}
    
    def check_vulnerabilities(self, package_name: str, version: str = None) -> List[Dict]:
        """Check for known vulnerabilities"""
        cache_key = f"{package_name}@{version}" if version else package_name
        
        if cache_key in self.vuln_data:
            cached = self.vuln_data[cache_key]
            cached_time = datetime.fromisoformat(cached['cached_at'])
            
            if datetime.now() - cached_time < timedelta(hours=6):
                return cached['vulnerabilities']
        
        vulnerabilities = []
        
        try:
            query = {
                "package": {
                    "name": package_name,
                    "ecosystem": "PyPI"
                }
            }
            
            if version:
                query["version"] = version
            
            response = requests.post(
                "https://api.osv.dev/v1/query",
                json=query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'vulns' in data:
                    vulnerabilities.extend(data['vulns'])
            
            if version:
                response = requests.get(
                    f"https://pyup.io/api/v1/vulnerabilities/{package_name}/",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for vuln in data:
                        if vuln.get('affected_versions'):
                            vulnerabilities.append({
                                'id': vuln.get('cve', ''),
                                'summary': vuln.get('advisory', ''),
                                'severity': vuln.get('severity', 'unknown'),
                                'source': 'pyup'
                            })
            
            self.vuln_data[cache_key] = {
                'cached_at': datetime.now().isoformat(),
                'vulnerabilities': vulnerabilities
            }
            
        except Exception as e:
            print(f"[WARN] Error checking vulnerabilities for {package_name}: {e}")
        
        return vulnerabilities
    
    def calculate_health_score(self, package_info: Dict, vulnerabilities: List[Dict]) -> Dict:
        """Calculate health score for package"""
        score = 100
        reasons = []
        
        if not package_info:
            return {
                'score': 0,
                'reasons': ['No package info available'],
                'details': {}
            }
        
        info = package_info.get('info', {})
        releases = package_info.get('releases', {})
        
        if releases:
            release_dates = []
            for version, files in releases.items():
                if files and 'upload_time' in files[0]:
                    release_dates.append(datetime.fromisoformat(files[0]['upload_time'].replace('Z', '+00:00')))
            
            if release_dates:
                latest_release = max(release_dates)
                days_since_release = (datetime.now() - latest_release).days
                
                if days_since_release > 365:
                    score -= 20
                    reasons.append(f"No release in {days_since_release} days")
                elif days_since_release > 180:
                    score -= 10
                    reasons.append(f"No release in {days_since_release} days")
        
        try:
            response = requests.get(
                f"https://pypistats.org/api/packages/{info.get('name', '')}/recent",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                downloads = data.get('data', {}).get('last_month', 0)
                
                if downloads < 1000:
                    score -= 15
                    reasons.append(f"Low downloads: {downloads}/month")
                elif downloads < 10000:
                    score -= 5
                    reasons.append(f"Moderate downloads: {downloads}/month")
        except:
            pass
        
        if vulnerabilities:
            vuln_count = len(vulnerabilities)
            score -= min(vuln_count * 10, 50)
            
            critical = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
            high = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
            
            reasons.append(f"Found {vuln_count} vulnerabilities ({critical} critical, {high} high)")
        
        if info.get('classifiers'):
            classifiers = info['classifiers']
            
            if 'Development Status :: 1 - Planning' in classifiers:
                score -= 30
                reasons.append("Project in planning stage")
            elif 'Development Status :: 2 - Pre-Alpha' in classifiers:
                score -= 25
                reasons.append("Project in pre-alpha")
            elif 'Development Status :: 3 - Alpha' in classifiers:
                score -= 15
                reasons.append("Project in alpha")
            elif 'Development Status :: 4 - Beta' in classifiers:
                score -= 5
                reasons.append("Project in beta")
            elif 'Development Status :: 6 - Mature' in classifiers:
                score += 5
                reasons.append("Mature project")
            elif 'Development Status :: 7 - Inactive' in classifiers:
                score -= 40
                reasons.append("Project inactive")
        
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'reasons': reasons,
            'details': {
                'name': info.get('name'),
                'version': info.get('version'),
                'author': info.get('author'),
                'license': info.get('license'),
                'release_count': len(releases),
                'has_docs': bool(info.get('description')),
                'has_homepage': bool(info.get('home_page'))
            }
        }
    
    def check_all_packages(self) -> List[Dict]:
        """Check health of all packages"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_package = {
                executor.submit(self._check_single_package, pkg): pkg 
                for pkg in self.packages
            }
            
            for future in concurrent.futures.as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'package': package['name'],
                        'error': str(e),
                        'health_score': 0
                    })
        
        results.sort(key=lambda x: x.get('health_score', 0))
        return results
    
    def _check_single_package(self, package: Dict) -> Dict:
        """Check single package health"""
        name = package['name']
        version = package['version']
        
        print(f"[CHECK] {name}...")
        
        package_info = self.get_package_info(name)
        vulnerabilities = self.check_vulnerabilities(name, version)
        health = self.calculate_health_score(package_info, vulnerabilities)
        
        latest_version = None
        if package_info and 'info' in package_info:
            latest_version = package_info['info'].get('version')
        
        needs_update = False
        if version and latest_version and version != latest_version:
            needs_update = True
        
        return {
            'package': name,
            'current_version': version,
            'latest_version': latest_version,
            'needs_update': needs_update,
            'health_score': health['score'],
            'health_reasons': health['reasons'],
            'details': health['details'],
            'vulnerabilities': len(vulnerabilities),
            'vulnerability_details': vulnerabilities[:5],
            'checked_at': datetime.now().isoformat()
        }
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate HTML report"""
        total = len(results)
        critical = sum(1 for r in results if r['health_score'] < 50)
        warning = sum(1 for r in results if 50 <= r['health_score'] < 70)
        good = sum(1 for r in results if r['health_score'] >= 70)
        vulnerable = sum(1 for r in results if r['vulnerabilities'] > 0)
        needs_update = sum(1 for r in results if r.get('needs_update', False))
        
        html_rows = ""
        for result in results:
            score_class = "score-0" if result['health_score'] < 50 else "score-1" if result['health_score'] < 70 else "score-2"
            update_indicator = " [UPDATE]" if result.get('needs_update') else ""
            
            issues = "<ul style='margin:0;padding-left:20px;'>"
            for reason in result['health_reasons'][:3]:
                issues += f"<li>{reason}</li>"
            if result['vulnerabilities'] > 0:
                for vuln in result['vulnerability_details'][:2]:
                    issues += f"<li class='vuln'>Vuln: {vuln.get('id', 'Unknown')}</li>"
            issues += "</ul>"
            
            html_rows += f"""
            <tr>
                <td><strong>{result['package']}</strong></td>
                <td>{result['current_version'] or 'N/A'}</td>
                <td>{result.get('latest_version', 'N/A')}{update_indicator}</td>
                <td class="score {score_class}">{result['health_score']:.1f}</td>
                <td class="{'vuln' if result['vulnerabilities'] > 0 else ''}">{result['vulnerabilities']}</td>
                <td>{issues}</td>
            </tr>"""
        
        recommendations = ""
        if critical > 0:
            recommendations += f"<li class='critical'>Immediate action required for {critical} packages with critical health scores</li>"
        if vulnerable > 0:
            recommendations += f"<li class='vuln'>Update {vulnerable} packages with known vulnerabilities</li>"
        if needs_update > 0:
            recommendations += f"<li>Update {needs_update} packages to latest versions</li>"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dependency Health Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .critical {{ color: #721c24; background: #f8d7da; padding: 10px; border-radius: 5px; }}
        .warning {{ color: #856404; background: #fff3cd; padding: 10px; border-radius: 5px; }}
        .good {{ color: #155724; background: #d4edda; padding: 10px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .score {{ font-weight: bold; }}
        .score-0 {{ color: #721c24; }}
        .score-1 {{ color: #856404; }}
        .score-2 {{ color: #155724; }}
        .vuln {{ color: #721c24; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Dependency Health Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Packages: {total}</p>
        <p class="critical">Critical: {critical}</p>
        <p class="warning">Warning: {warning}</p>
        <p class="good">Good: {good}</p>
        <p class="vuln">Packages with Vulnerabilities: {vulnerable}</p>
        <p>Updates Available: {needs_update}</p>
    </div>
    
    <h2>Package Details</h2>
    <table>
        <tr>
            <th>Package</th><th>Version</th><th>Latest</th><th>Health Score</th><th>Vulns</th><th>Issues</th>
        </tr>
        {html_rows}
    </table>
    
    <h2>Recommendations</h2>
    <ul>{recommendations}</ul>
</body>
</html>"""
        
        report_file = self.report_dir / f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        latest_file = self.report_dir / "latest_report.html"
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(report_file)
    
    def check_for_failures(self, results: List[Dict], thresholds: Dict = None) -> bool:
        """Check if any package fails thresholds"""
        if thresholds is None:
            thresholds = {
                'min_score': 50,
                'max_vulnerabilities': 2,
                'critical_vulnerabilities': 0
            }
        
        failed = False
        
        for result in results:
            if result['health_score'] < thresholds['min_score']:
                print(f"[FAIL] {result['package']}: Health score {result['health_score']} below {thresholds['min_score']}")
                failed = True
            
            if result['vulnerabilities'] > thresholds['max_vulnerabilities']:
                print(f"[FAIL] {result['package']}: Too many vulnerabilities ({result['vulnerabilities']})")
                failed = True
            
            critical = sum(1 for v in result['vulnerability_details'] if v.get('severity') == 'critical')
            if critical > thresholds.get('critical_vulnerabilities', 0):
                print(f"[FAIL] {result['package']}: Found {critical} critical vulnerabilities")
                failed = True
        
        return failed

def main():
    parser = argparse.ArgumentParser(description="Dependency Health Check")
    parser.add_argument("--check-all", action="store_true", help="Check all dependencies")
    parser.add_argument("--generate-report", action="store_true", help="Generate HTML report")
    parser.add_argument("--fail-on-issues", action="store_true", help="Fail if issues found")
    parser.add_argument("--output-json", type=str, help="Output results to JSON file")
    
    args = parser.parse_args()
    checker = DependencyHealthCheck()
    
    if args.check_all:
        print("CHECKING ALL DEPENDENCIES...")
        results = checker.check_all_packages()
        
        print("\n" + "="*60)
        print("DEPENDENCY HEALTH SUMMARY")
        print("="*60)
        
        for result in results:
            status = "OK" if result['health_score'] >= 70 else "WARN" if result['health_score'] >= 50 else "FAIL"
            vuln = f"({result['vulnerabilities']} vulns)" if result['vulnerabilities'] > 0 else ""
            update = " [UPDATE]" if result.get('needs_update') else ""
            print(f"{status} {result['package']}: {result['health_score']:.1f}{vuln}{update}")
        
        if args.generate_report:
            report = checker.generate_report(results)
            print(f"\nReport generated: {report}")
        
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output_json}")
        
        if args.fail_on_issues:
            if checker.check_for_failures(results):
                print("\n[FAIL] Dependency health check failed!")
                sys.exit(1)
            else:
                print("\n[OK] All dependencies meet thresholds")

if __name__ == "__main__":
    main()
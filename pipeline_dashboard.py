"""
Pipeline Dashboard - Track and visualize pipeline metrics
Phase 1 Feature: Pipeline Metrics & Dashboard
"""

import os
import sys
import json
import sqlite3
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class PipelineDashboard:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / 'pipeline-metrics.db'
        self.dashboard_dir = self.base_dir / 'dashboard'
        self.dashboard_dir.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE,
                timestamp TEXT,
                branch TEXT,
                commit_hash TEXT,
                commit_message TEXT,
                author TEXT,
                status TEXT,
                duration REAL,
                triggered_by TEXT,
                pipeline_type TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS step_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                step_name TEXT,
                step_index INTEGER,
                duration REAL,
                status TEXT,
                start_time TEXT,
                end_time TEXT,
                FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                total_tests INTEGER,
                passed INTEGER,
                failed INTEGER,
                skipped INTEGER,
                coverage REAL,
                duration REAL,
                FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                function_name TEXT,
                execution_time REAL,
                memory_used REAL,
                cpu_used REAL,
                timestamp TEXT,
                FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_run(self, data: Dict[str, Any]):
        """Record pipeline run metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pipeline_runs 
            (run_id, timestamp, branch, commit_hash, commit_message, author, status, duration, triggered_by, pipeline_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('run_id'),
            data.get('timestamp', datetime.now().isoformat()),
            data.get('branch'),
            data.get('commit_hash'),
            data.get('commit_message'),
            data.get('author'),
            data.get('status'),
            data.get('duration'),
            data.get('triggered_by'),
            data.get('pipeline_type')
        ))
        
        for i, step in enumerate(data.get('steps', [])):
            cursor.execute('''
                INSERT INTO step_metrics 
                (run_id, step_name, step_index, duration, status, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('run_id'),
                step.get('name'),
                i,
                step.get('duration'),
                step.get('status'),
                step.get('start_time'),
                step.get('end_time')
            ))
        
        if 'test_results' in data:
            tests = data['test_results']
            cursor.execute('''
                INSERT INTO test_results 
                (run_id, total_tests, passed, failed, skipped, coverage, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('run_id'),
                tests.get('total', 0),
                tests.get('passed', 0),
                tests.get('failed', 0),
                tests.get('skipped', 0),
                tests.get('coverage', 0),
                tests.get('duration', 0)
            ))
        
        conn.commit()
        conn.close()
    
    def get_metrics(self, days: int = 30) -> Dict:
        """Get pipeline metrics for last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END),
                   AVG(duration), MIN(duration), MAX(duration)
            FROM pipeline_runs WHERE timestamp > ?
        ''', (since,))
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT DATE(timestamp), COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), AVG(duration)
            FROM pipeline_runs WHERE timestamp > ? GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)
        ''', (since,))
        daily = cursor.fetchall()
        
        cursor.execute('''
            SELECT branch, COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), AVG(duration)
            FROM pipeline_runs WHERE timestamp > ? GROUP BY branch ORDER BY COUNT(*) DESC
        ''', (since,))
        branches = cursor.fetchall()
        
        cursor.execute('''
            SELECT step_name, COUNT(*), AVG(duration), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)
            FROM step_metrics WHERE run_id IN (SELECT run_id FROM pipeline_runs WHERE timestamp > ?)
            GROUP BY step_name ORDER BY AVG(duration) DESC
        ''', (since,))
        steps = cursor.fetchall()
        
        cursor.execute('''
            SELECT DATE(p.timestamp), AVG(t.coverage), AVG(t.passed), AVG(t.failed)
            FROM test_results t JOIN pipeline_runs p ON t.run_id = p.run_id
            WHERE p.timestamp > ? GROUP BY DATE(p.timestamp) ORDER BY DATE(p.timestamp)
        ''', (since,))
        test_trends = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_runs': stats[0] or 0,
            'successful_runs': stats[1] or 0,
            'success_rate': (stats[1] / stats[0] * 100) if stats[0] else 0,
            'avg_duration': stats[2] or 0,
            'min_duration': stats[3] or 0,
            'max_duration': stats[4] or 0,
            'daily': daily,
            'branches': branches,
            'steps': steps,
            'test_trends': test_trends
        }
    
    def generate_dashboard(self, days: int = 30) -> str:
        """Generate interactive HTML dashboard"""
        metrics = self.get_metrics(days)
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Daily Pipeline Runs', 'Success Rate by Branch',
                          'Step Duration', 'Test Coverage Trend',
                          'Pipeline Duration Trend', 'Step Success Rate'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'bar'}]]
        )
        
        if metrics['daily']:
            dates = [d[0] for d in metrics['daily']]
            runs = [d[1] for d in metrics['daily']]
            success = [d[2] for d in metrics['daily']]
            
            fig.add_trace(go.Bar(name='Total Runs', x=dates, y=runs, marker_color='lightblue'), row=1, col=1)
            fig.add_trace(go.Bar(name='Successful', x=dates, y=success, marker_color='lightgreen'), row=1, col=1)
        
        if metrics['branches']:
            branches = [b[0] for b in metrics['branches'][:10]]
            success_rate = [(b[2] / b[1] * 100) if b[1] else 0 for b in metrics['branches'][:10]]
            colors = ['green' if r > 80 else 'orange' if r > 60 else 'red' for r in success_rate]
            fig.add_trace(go.Bar(name='Success Rate %', x=branches, y=success_rate, marker_color=colors), row=1, col=2)
        
        if metrics['steps']:
            steps = [s[0][:30] + '...' if len(s[0]) > 30 else s[0] for s in metrics['steps'][:10]]
            durations = [s[2] for s in metrics['steps'][:10]]
            fig.add_trace(go.Bar(name='Avg Duration (s)', x=steps, y=durations, marker_color='purple'), row=2, col=1)
        
        if metrics['test_trends']:
            dates = [t[0] for t in metrics['test_trends']]
            coverage = [t[1] for t in metrics['test_trends']]
            fig.add_trace(go.Scatter(name='Coverage %', x=dates, y=coverage, mode='lines+markers',
                          line=dict(color='green', width=2)), row=2, col=2)
            fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Minimum 85%", row=2, col=2)
        
        if metrics['daily']:
            dates = [d[0] for d in metrics['daily']]
            avg_duration = [d[3] for d in metrics['daily']]
            fig.add_trace(go.Scatter(name='Avg Duration (s)', x=dates, y=avg_duration,
                          mode='lines+markers', line=dict(color='blue', width=2)), row=3, col=1)
        
        if metrics['steps']:
            steps = [s[0][:20] + '...' if len(s[0]) > 20 else s[0] for s in metrics['steps']]
            success_rate = [(s[3] / s[1] * 100) if s[1] else 0 for s in metrics['steps']]
            colors = ['green' if r > 90 else 'orange' if r > 70 else 'red' for r in success_rate]
            fig.add_trace(go.Bar(name='Success Rate %', x=steps, y=success_rate, marker_color=colors), row=3, col=2)
        
        fig.update_layout(title_text=f"Pipeline Dashboard - Last {days} Days", height=1200, showlegend=True, template='plotly_white')
        fig.update_xaxes(tickangle=45)
        
        stats_html = f"""
        <div class="stats">
            <div class="stat-card"><div class="stat-value">{metrics['total_runs']}</div><div class="stat-label">Total Pipeline Runs</div></div>
            <div class="stat-card"><div class="stat-value {('success' if metrics['success_rate'] > 80 else 'warning' if metrics['success_rate'] > 60 else 'danger')}">{metrics['success_rate']:.1f}%</div><div class="stat-label">Success Rate</div></div>
            <div class="stat-card"><div class="stat-value">{metrics['avg_duration']:.1f}s</div><div class="stat-label">Average Duration</div></div>
            <div class="stat-card"><div class="stat-value">{metrics['max_duration']:.1f}s</div><div class="stat-label">Max Duration</div></div>
        </div>
        """
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                 gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px;
                     box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 36px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 10px; }}
        .success {{ color: #28a745; }} .warning {{ color: #ffc107; }} .danger {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Pipeline Analytics Dashboard</h1>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    {stats_html}
    <div class="dashboard">{fig.to_html(full_html=False, include_plotlyjs=False)}</div>
    <script>setTimeout(function(){{ location.reload(); }}, 300000);</script>
</body>
</html>"""
        
        dashboard_file = self.dashboard_dir / 'dashboard.html'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(dashboard_file)
    
    def simulate_pipeline_data(self):
        """Generate sample data for testing"""
        branches = ['main', 'develop', 'feature/new-ui', 'bugfix/login', 'hotfix/security']
        statuses = ['success', 'success', 'success', 'failed', 'success']
        step_names = ['Lint & Format', 'Type Checking', 'Security Scan', 'Tests', 'Complexity Check']
        
        for i in range(100):
            timestamp = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            run_id = f"run_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                'run_id': run_id,
                'timestamp': timestamp.isoformat(),
                'branch': random.choice(branches),
                'commit_hash': f"abc{random.randint(100, 999)}def",
                'commit_message': f"Test commit {i}",
                'author': f"user{random.randint(1,5)}@example.com",
                'status': random.choice(statuses),
                'duration': random.uniform(60, 300),
                'triggered_by': 'pull_request' if random.random() > 0.5 else 'push',
                'pipeline_type': 'PR' if random.random() > 0.5 else 'CI',
                'steps': []
            }
            
            step_start = 0
            for j, step_name in enumerate(step_names):
                step_duration = random.uniform(10, 60)
                step_status = 'success' if random.random() > 0.1 else 'failed'
                run_data['steps'].append({
                    'name': step_name,
                    'duration': step_duration,
                    'status': step_status,
                    'start_time': (timestamp + timedelta(seconds=step_start)).isoformat(),
                    'end_time': (timestamp + timedelta(seconds=step_start + step_duration)).isoformat()
                })
                step_start += step_duration
            
            if random.random() > 0.3:
                total = random.randint(50, 200)
                passed = int(total * random.uniform(0.8, 1.0))
                failed = total - passed - random.randint(0, 5)
                run_data['test_results'] = {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'skipped': total - passed - failed,
                    'coverage': random.uniform(70, 95),
                    'duration': random.uniform(20, 60)
                }
            
            self.record_run(run_data)
        
        print("Sample data generated")

def main():
    parser = argparse.ArgumentParser(description="Pipeline Dashboard")
    parser.add_argument("--record-metrics", action="store_true", help="Record pipeline metrics")
    parser.add_argument("--generate-dashboard", action="store_true", help="Generate dashboard HTML")
    parser.add_argument("--simulate-data", action="store_true", help="Generate sample data for testing")
    parser.add_argument("--days", type=int, default=30, help="Number of days to include")
    
    args = parser.parse_args()
    dashboard = PipelineDashboard()
    
    if args.simulate_data:
        dashboard.simulate_pipeline_data()
    
    if args.generate_dashboard:
        dashboard_file = dashboard.generate_dashboard(args.days)
        print(f"Dashboard generated: {dashboard_file}")
    
    if args.record_metrics:
        run_data = {
            'run_id': os.environ.get('BITBUCKET_BUILD_NUMBER', 'local'),
            'branch': os.environ.get('BITBUCKET_BRANCH', 'local'),
            'commit_hash': os.environ.get('BITBUCKET_COMMIT', ''),
            'commit_message': os.environ.get('BITBUCKET_COMMIT_MESSAGE', ''),
            'author': os.environ.get('BITBUCKET_STEP_TRIGGERER_UUID', ''),
            'status': 'success' if os.environ.get('BITBUCKET_EXIT_CODE', '0') == '0' else 'failed',
            'duration': 0,
            'triggered_by': 'pull_request' if os.environ.get('BITBUCKET_PR_ID') else 'push',
            'pipeline_type': 'PR' if os.environ.get('BITBUCKET_PR_ID') else 'CI',
            'steps': []
        }
        dashboard.record_run(run_data)
        print("Metrics recorded")

if __name__ == "__main__":
    main()
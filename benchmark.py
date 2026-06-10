import time
import json
import torch
import os
import random
import statistics
import argparse
from nql.engine import ERPBot

class BenchmarkSuite:
    def __init__(self, connection_url="sqlite:///test_suite.db"):
        self.connection_url = connection_url
        if "test_suite.db" in connection_url:
            self._setup_test_db()
        self.bot = ERPBot(connection_url)

    def _setup_test_db(self):
        from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
        from sqlalchemy.orm import declarative_base
        Base = declarative_base()
        
        class Student(Base):
            __tablename__ = 'students'
            id = Column(Integer, primary_key=True)
            name = Column(String)
            marks = Column(Integer)
            
        engine = create_engine(self.connection_url)
        Base.metadata.create_all(engine)

    def run_file(self, dataset_path: str):
        print(f"\n🚀 Running Benchmark: {os.path.basename(dataset_path)}")
        if not os.path.exists(dataset_path):
            print(f"❌ Error: File {dataset_path} not found.")
            return None

        with open(dataset_path, 'r') as f:
            samples = json.load(f)

        latencies = []
        sql_correct = 0
        total = len(samples)
        
        print("-" * 70)
        print(f"{'Question':<40} | {'Lat':<7} | {'SQL'}")
        print("-" * 70)

        for s in samples:
            question = s['question']
            expected_sql = s.get('expected_sql', "")
            
            start = time.perf_counter()
            response = self.bot.ask(question)
            end = time.perf_counter()
            
            latency = (end - start) * 1000
            latencies.append(latency)
            
            # Simple SQL comparison (ignoring case and whitespace)
            is_sql_correct = response.sql.lower().replace(" ", "") == expected_sql.lower().replace(" ", "")
            if is_sql_correct:
                sql_correct += 1
            
            status = "✅" if is_sql_correct else "❌"
            print(f"{question[:40]:<40} | {latency:>5.1f}ms | {status}")

        if not latencies:
            return None

        results = {
            "total": total,
            "sql_accuracy": (sql_correct / total) * 100 if total > 0 else 0,
            "avg_latency": statistics.mean(latencies),
            "p50_latency": statistics.median(latencies),
            "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else latencies[-1],
            "p99_latency": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else latencies[-1]
        }
        
        self.print_results(results)
        return results

    def print_results(self, r):
        print("-" * 70)
        print(f"📊 FINAL RESULTS:")
        print(f"SQL Accuracy: {r['sql_accuracy']:.1f}%")
        print(f"Latency P50:  {r['p50_latency']:.2f}ms")
        print(f"Latency P95:  {r['p95_latency']:.2f}ms")
        print(f"Latency P99:  {r['p99_latency']:.2f}ms")
        print("-" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to benchmark JSON file")
    parser.add_argument("--db", type=str, default="sqlite:///test_suite.db", help="Database connection URL")
    args = parser.parse_args()

    suite = BenchmarkSuite(args.db)
    if args.file:
        suite.run_file(args.file)
    else:
        # Run all in benchmarks/ directory if none specified
        benchmark_dir = "benchmarks"
        if os.path.exists(benchmark_dir):
            files = [os.path.join(benchmark_dir, f) for f in os.listdir(benchmark_dir) if f.endswith(".json")]
            for f in files:
                suite.run_file(f)
        else:
            print("No benchmark files found in benchmarks/ and --file not provided.")

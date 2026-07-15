"""
Latency Benchmark for Multi-Agent RAG Pipeline (Tech E-Commerce).

Measures per-stage and end-to-end latency across 10 sample queries.
Sends HTTP requests to the running services to measure realistic
production latency including network overhead between agents.

Pipeline under test:
  User -> Host Agent (intent classification)
       -> Advisor Agent (RAG orchestration)
            -> Search Agent (embedding + Qdrant retrieval)
            -> LLM generation (GPT-4o-mini)
       -> Response

Usage:
    Ensure all services are running (Host:8000, Search:8001, Advisor:8002, Redis, Qdrant).
    cd d:/CaNhan/tech-ecommerce-system
    python tests/latency/run_latency_benchmark.py
"""

import time
import json
import asyncio
import statistics
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


# =========================================================
# Service Endpoints
# =========================================================

HOST_AGENT_URL = "http://localhost:8000"
SEARCH_AGENT_URL = "http://localhost:8001"
ADVISOR_AGENT_URL = "http://localhost:8002"


# =========================================================
# 10 Sample Questions (diverse product categories and intents)
# =========================================================

BENCHMARK_QUESTIONS = [
    {
        "id": "Q01",
        "category": "action_camera",
        "question": "Tìm camera hành trình GoPro Hero 13",
    },
    {
        "id": "Q02",
        "category": "ip_camera",
        "question": "Tư vấn mua camera IP WiFi Ezviz 360 độ trong nhà",
    },
    {
        "id": "Q03",
        "category": "gimbal",
        "question": "Tay cầm chống rung Gimbal DJI OM 6 có tốt không?",
    },
    {
        "id": "Q04",
        "category": "car_accessory",
        "question": "Bộ HUD kính lái VIETMAP hiển thị thông tin gì?",
    },
    {
        "id": "Q05",
        "category": "action_camera",
        "question": "So sánh Insta360 X4 và GoPro",
    },
    {
        "id": "Q06",
        "category": "outdoor_camera",
        "question": "Camera an ninh ngoài trời dùng năng lượng mặt trời",
    },
    {
        "id": "Q07",
        "category": "gimbal",
        "question": "DJI Ronin RS4 mini dùng cho máy ảnh chịu tải bao nhiêu?",
    },
    {
        "id": "Q08",
        "category": "tripod",
        "question": "Gậy chụp ảnh Tripod Wiwu loại nào giá rẻ?",
    },
    {
        "id": "Q09",
        "category": "car_accessory",
        "question": "Android Box xe hơi VIETMAP cấu hình như thế nào?",
    },
    {
        "id": "Q10",
        "category": "general",
        "question": "Gợi ý một số camera hành động chống nước để đi bơi",
    },
]


# =========================================================
# HTTP Client Helpers
# =========================================================

async def check_service_health(client: httpx.AsyncClient, url: str, name: str) -> bool:
    """Check if a service is online before running the benchmark."""
    try:
        resp = await client.get(f"{url}/health", timeout=5.0)
        data = resp.json()
        status = data.get("status", "unknown")
        print(f"  {name:20s} -> {status}")
        return status in ("online", "initializing")
    except Exception as e:
        print(f"  {name:20s} -> OFFLINE ({e})")
        return False


async def measure_search_agent(client: httpx.AsyncClient, query: str) -> Dict[str, Any]:
    """Call Search Agent directly and measure retrieval latency."""
    start = time.perf_counter()
    resp = await client.post(
        f"{SEARCH_AGENT_URL}/api/search",
        json={"query": query, "limit": 3},
        timeout=30.0,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()
    return {
        "latency_s": round(elapsed, 4),
        "total_found": data.get("total_found", 0),
        "results": data.get("results", []),
    }


async def measure_advisor_agent(client: httpx.AsyncClient, session_id: str, message: str) -> Dict[str, Any]:
    """Call Advisor Agent directly and measure RAG latency (retrieval + LLM)."""
    start = time.perf_counter()
    resp = await client.post(
        f"{ADVISOR_AGENT_URL}/api/chat",
        json={"session_id": session_id, "message": message},
        timeout=60.0,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()
    return {
        "latency_s": round(elapsed, 4),
        "content": data.get("content", ""),
        "referenced_products": data.get("referenced_products", ""),
    }


async def measure_host_agent(client: httpx.AsyncClient, session_id: str, message: str) -> Dict[str, Any]:
    """Call Host Agent (full pipeline) and measure end-to-end latency."""
    start = time.perf_counter()
    resp = await client.post(
        f"{HOST_AGENT_URL}/api/orchestrate",
        json={"message": message, "session_id": session_id},
        timeout=90.0,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()
    return {
        "latency_s": round(elapsed, 4),
        "agent": data.get("agent", "unknown"),
        "data": data.get("data", {}),
    }


# =========================================================
# Single Query Runner
# =========================================================

async def run_single_query(client: httpx.AsyncClient, question_data: dict, index: int) -> Dict[str, Any]:
    """Run one query through all pipeline stages and collect timing data."""
    session_id = f"benchmark_{question_data['id']}_{int(time.time())}"
    question = question_data["question"]

    result = {
        "question_id": question_data["id"],
        "category": question_data["category"],
        "question": question,
        "session_id": session_id,
        "stage_latencies_s": {},
        "e2e_latency_s": 0,
        "search_results_count": 0,
        "advisor_answer": "",
        "referenced_products": "",
        "routed_agent": "",
        "error": None,
    }

    try:
        # Stage 1: Retrieval only (Search Agent direct call)
        print(f"    [1/3] Search Agent (retrieval)...", end="", flush=True)
        search_result = await measure_search_agent(client, question)
        result["stage_latencies_s"]["retrieval"] = search_result["latency_s"]
        result["search_results_count"] = search_result["total_found"]
        print(f" {search_result['latency_s']:.4f}s ({search_result['total_found']} docs)")

        # Stage 2: Advisor Agent (retrieval + LLM generation)
        print(f"    [2/3] Advisor Agent (retrieval + LLM)...", end="", flush=True)
        advisor_result = await measure_advisor_agent(client, session_id, question)
        result["stage_latencies_s"]["advisor_total"] = advisor_result["latency_s"]
        result["advisor_answer"] = advisor_result["content"]
        result["referenced_products"] = advisor_result["referenced_products"]

        # Estimate LLM generation time by subtracting retrieval from advisor total
        llm_estimate = max(0, advisor_result["latency_s"] - search_result["latency_s"])
        result["stage_latencies_s"]["llm_generation_est"] = round(llm_estimate, 4)
        print(f" {advisor_result['latency_s']:.4f}s (LLM est: {llm_estimate:.4f}s)")

        # Stage 3: Full pipeline via Host Agent (intent + routing + advisor)
        print(f"    [3/3] Host Agent (full E2E)...", end="", flush=True)
        # Use a different session to avoid chat history interference
        e2e_session = f"benchmark_e2e_{question_data['id']}_{int(time.time())}"
        host_result = await measure_host_agent(client, e2e_session, question)
        result["stage_latencies_s"]["e2e_via_host"] = host_result["latency_s"]
        result["e2e_latency_s"] = host_result["latency_s"]
        result["routed_agent"] = host_result["agent"]

        # Estimate intent classification overhead
        intent_overhead = max(0, host_result["latency_s"] - advisor_result["latency_s"])
        result["stage_latencies_s"]["intent_classification_est"] = round(intent_overhead, 4)
        print(f" {host_result['latency_s']:.4f}s (intent overhead est: {intent_overhead:.4f}s)")

    except httpx.HTTPStatusError as e:
        result["error"] = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        print(f" ERROR: {result['error']}")
    except httpx.RequestError as e:
        result["error"] = f"Connection error: {str(e)}"
        print(f" ERROR: {result['error']}")
    except Exception as e:
        result["error"] = str(e)
        print(f" ERROR: {result['error']}")

    return result


# =========================================================
# Aggregation and Statistics
# =========================================================

def compute_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate statistics from individual query results."""

    e2e_times = [r["e2e_latency_s"] for r in results]

    # Collect all stage names across results
    all_stages = set()
    for r in results:
        all_stages.update(r["stage_latencies_s"].keys())

    # Per-stage statistics
    stage_stats = {}
    for stage in sorted(all_stages):
        values = [
            r["stage_latencies_s"][stage]
            for r in results
            if stage in r["stage_latencies_s"]
        ]
        if values:
            stage_stats[stage] = {
                "mean_s": round(statistics.mean(values), 4),
                "median_s": round(statistics.median(values), 4),
                "min_s": round(min(values), 4),
                "max_s": round(max(values), 4),
                "stdev_s": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
                "count": len(values),
            }

    # Identify the slowest stage on average
    slowest_stage = max(stage_stats, key=lambda s: stage_stats[s]["mean_s"]) if stage_stats else "N/A"

    # Docs retrieved stats
    doc_counts = [r["search_results_count"] for r in results]

    return {
        "total_queries": len(results),
        "e2e_stats": {
            "mean_s": round(statistics.mean(e2e_times), 4),
            "median_s": round(statistics.median(e2e_times), 4),
            "min_s": round(min(e2e_times), 4),
            "max_s": round(max(e2e_times), 4),
            "stdev_s": round(statistics.stdev(e2e_times), 4) if len(e2e_times) > 1 else 0,
            "p90_s": round(sorted(e2e_times)[int(len(e2e_times) * 0.9)], 4),
            "p95_s": round(sorted(e2e_times)[min(int(len(e2e_times) * 0.95), len(e2e_times) - 1)], 4),
        },
        "per_stage_stats": stage_stats,
        "slowest_stage": slowest_stage,
        "slowest_stage_mean_s": stage_stats.get(slowest_stage, {}).get("mean_s", 0),
        "docs_retrieved": {
            "mean": round(statistics.mean(doc_counts), 2),
            "min": min(doc_counts),
            "max": max(doc_counts),
        },
    }


# =========================================================
# Markdown Report Generator
# =========================================================

def format_report(results: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
    """Build a human-readable markdown report from benchmark results."""
    lines = []
    lines.append("# Multi-Agent RAG Pipeline Latency Benchmark Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total queries: {stats['total_queries']}")
    lines.append("")
    lines.append("## Pipeline Architecture")
    lines.append("")
    lines.append("```")
    lines.append("User -> Host Agent (GPT-4o-mini intent classification)")
    lines.append("     -> Advisor Agent (RAG orchestrator)")
    lines.append("          -> Search Agent (MiniLM embedding + Qdrant vector search)")
    lines.append("          -> GPT-4o-mini (answer generation with product context)")
    lines.append("     -> Response")
    lines.append("```")

    # End-to-end summary
    lines.append("\n## 1. End-to-End Latency Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for key, val in stats["e2e_stats"].items():
        label = key.replace("_s", "").replace("_", " ").upper()
        lines.append(f"| {label} | {val:.4f}s |")

    # Per-stage breakdown
    lines.append("\n## 2. Per-Stage Latency Breakdown (seconds)")
    lines.append("")
    lines.append("| Stage | Mean | Median | Min | Max | Stdev | Runs |")
    lines.append("|-------|------|--------|-----|-----|-------|------|")
    for name, s in stats["per_stage_stats"].items():
        lines.append(
            f"| {name} | {s['mean_s']:.4f} | {s['median_s']:.4f} | "
            f"{s['min_s']:.4f} | {s['max_s']:.4f} | {s['stdev_s']:.4f} | {s['count']} |"
        )

    # Slowest stage
    lines.append(f"\n**Slowest stage (avg):** `{stats['slowest_stage']}` at {stats['slowest_stage_mean_s']:.4f}s")

    # Retrieval stats
    lines.append("\n## 3. Retrieval Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Mean docs retrieved | {stats['docs_retrieved']['mean']:.1f} |")
    lines.append(f"| Min docs retrieved | {stats['docs_retrieved']['min']} |")
    lines.append(f"| Max docs retrieved | {stats['docs_retrieved']['max']} |")

    # Per-query detail
    lines.append("\n## 4. Per-Query Detail")
    lines.append("")

    for i, r in enumerate(results):
        lines.append(f"### 4.{i+1}. [{r['question_id']}] {r['category'].upper()}")
        lines.append("")
        lines.append(f"**Question:** {r['question']}")
        lines.append("")

        if r.get("error"):
            lines.append(f"**Error:** {r['error']}")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        lines.append(f"**Answer (truncated):**")
        lines.append("")
        answer_preview = r["advisor_answer"][:300]
        if len(r["advisor_answer"]) > 300:
            answer_preview += "..."
        lines.append(f"> {answer_preview}")
        lines.append("")

        # Timing summary
        lines.append(f"**E2E Latency:** {r['e2e_latency_s']:.4f}s | "
                     f"Docs: {r['search_results_count']} | "
                     f"Routed to: `{r['routed_agent']}`")
        lines.append("")

        # Stage breakdown table
        lines.append("| Stage | Time (s) | % of E2E |")
        lines.append("|-------|----------|----------|")
        e2e = r["e2e_latency_s"] or 1
        for stage_name, stage_time in r["stage_latencies_s"].items():
            pct = (stage_time / e2e) * 100
            lines.append(f"| {stage_name} | {stage_time:.4f} | {pct:.1f}% |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Quick comparison table
    lines.append("## 5. Quick Comparison Table")
    lines.append("")
    lines.append("| ID | Category | Retrieval (s) | Advisor (s) | E2E (s) | Docs | Agent | Question |")
    lines.append("|----|----------|---------------|-------------|---------|------|-------|----------|")
    for r in results:
        retrieval_t = r["stage_latencies_s"].get("retrieval", 0)
        advisor_t = r["stage_latencies_s"].get("advisor_total", 0)
        q_short = r["question"][:45] + ("..." if len(r["question"]) > 45 else "")
        lines.append(
            f"| {r['question_id']} | {r['category']} | {retrieval_t:.4f} | "
            f"{advisor_t:.4f} | {r['e2e_latency_s']:.4f} | "
            f"{r['search_results_count']} | {r['routed_agent']} | {q_short} |"
        )

    return "\n".join(lines)


# =========================================================
# Main Entry Point
# =========================================================

async def main():
    print("=" * 60)
    print("  Multi-Agent RAG Pipeline Latency Benchmark")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Pre-flight: verify all services are online
        print("\n[HEALTH CHECK] Verifying service availability...")
        host_ok = await check_service_health(client, HOST_AGENT_URL, "Host Agent (8000)")
        search_ok = await check_service_health(client, SEARCH_AGENT_URL, "Search Agent (8001)")
        advisor_ok = await check_service_health(client, ADVISOR_AGENT_URL, "Advisor Agent (8002)")

        if not all([host_ok, search_ok, advisor_ok]):
            print("\n[ABORT] One or more services are offline. Start all agents before running.")
            print("  Required: Host(8000), Search(8001), Advisor(8002), Qdrant(6333), Redis(6379)")
            return

        print("\n[OK] All services online. Starting benchmark...\n")

        # Warm-up: send one throwaway request to eliminate cold-start bias
        print("[WARM-UP] Sending warm-up request to prime caches and connections...")
        try:
            await measure_search_agent(client, "test warm up query")
            await measure_advisor_agent(client, "warmup_session", "hello")
            print("[WARM-UP] Complete.\n")
        except Exception as e:
            print(f"[WARM-UP] Warning: {e}\n")

        # Run benchmark
        results = []
        for i, q in enumerate(BENCHMARK_QUESTIONS):
            print(f"\n--- [{i+1}/{len(BENCHMARK_QUESTIONS)}] {q['id']}: {q['question'][:55]}...")
            result = await run_single_query(client, q, i)
            results.append(result)

    # Filter valid results (no errors)
    valid_results = [r for r in results if r["error"] is None and r["e2e_latency_s"] > 0]

    if not valid_results:
        print("\n[ERROR] No valid results collected. Check service logs.")
        return

    # Compute aggregate statistics
    stats = compute_statistics(valid_results)

    # Save outputs
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON raw data
    json_path = output_dir / f"latency_raw_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "statistics": stats}, f, indent=2, ensure_ascii=False)

    # Markdown report
    report = format_report(results, stats)
    md_path = output_dir / f"latency_report_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[SAVED] Report:   {md_path}")
    print(f"[SAVED] Raw data: {json_path}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Queries run:           {stats['total_queries']}")
    print(f"  Mean E2E latency:      {stats['e2e_stats']['mean_s']:.4f}s")
    print(f"  Median E2E latency:    {stats['e2e_stats']['median_s']:.4f}s")
    print(f"  P90 E2E latency:       {stats['e2e_stats']['p90_s']:.4f}s")
    print(f"  P95 E2E latency:       {stats['e2e_stats']['p95_s']:.4f}s")
    print(f"  Min / Max E2E:         {stats['e2e_stats']['min_s']:.4f}s / {stats['e2e_stats']['max_s']:.4f}s")
    print(f"  Slowest stage (avg):   {stats['slowest_stage']} ({stats['slowest_stage_mean_s']:.4f}s)")
    print(f"  Avg docs retrieved:    {stats['docs_retrieved']['mean']:.1f}")

    # Per-stage breakdown
    print(f"\n  Stage breakdown (avg):")
    for name, s in stats["per_stage_stats"].items():
        bar_len = int(s["mean_s"] / stats["e2e_stats"]["mean_s"] * 30) if stats["e2e_stats"]["mean_s"] > 0 else 0
        bar = "#" * bar_len
        print(f"    {name:30s}: {s['mean_s']:.4f}s  {bar}")


if __name__ == "__main__":
    asyncio.run(main())

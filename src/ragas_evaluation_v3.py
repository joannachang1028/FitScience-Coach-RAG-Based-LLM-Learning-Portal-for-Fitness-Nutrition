#!/usr/bin/env python3
"""
RAGAs Evaluation Script for FitScience Coach
Using OpenAI API for reliable evaluation.
"""

import os
import json
import warnings
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    ContextRelevance,
)
from rag_pipeline import FitScienceRAG
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
warnings.filterwarnings("ignore")

# OpenAI API Key - Set via environment variable or replace with your key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-openai-api-key-here")
if OPENAI_API_KEY != "your-openai-api-key-here":
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ---------------------------------------------------------------------
# Evaluation dataset
# ---------------------------------------------------------------------
def create_evaluation_dataset():
    return [
        {
            "question": "How much protein should I eat per day for muscle building?",
            "ground_truth": "For resistance training, consume 1.6–2.2 g/kg body weight daily, spread across meals.",
            "contexts": [
                "Optimal intake for muscle growth is 1.6–2.2 g/kg/day distributed over multiple meals.",
                "Protein distribution across the day enhances synthesis and recovery efficiency.",
            ],
        },
        {
            "question": "What is the best workout split for beginners?",
            "ground_truth": "Full-body training three times per week is best for beginners before switching to upper/lower or push-pull-legs.",
            "contexts": [
                "Beginners progress best with full-body workouts 3 days per week.",
                "This schedule balances stimulus and recovery across muscle groups.",
            ],
        },
        {
            "question": "How do I calculate my BMR and TDEE?",
            "ground_truth": "Use the Harris–Benedict formula for BMR and multiply by activity factor (1.2–1.9) for TDEE.",
            "contexts": [
                "Harris–Benedict: Men = 88.362 + (13.397×wt) + (4.799×ht) – (5.677×age).",
                "TDEE = BMR × activity (1.2–1.9 depending on lifestyle).",
            ],
        },
        {
            "question": "How much sleep do I need for optimal recovery?",
            "ground_truth": "Adults 7–9 h; athletes 8–10 h. Deep sleep releases growth hormone aiding repair and immune function.",
            "contexts": [
                "Adults need 7–9 h; athletes 8–10 h.",
                "Deep sleep supports muscle protein synthesis and hormone release.",
            ],
        },
        {
            "question": "What are the most important micronutrients for athletes?",
            "ground_truth": "Iron, Vitamin D, Magnesium, Zinc, and B Vitamins are critical for performance and recovery.",
            "contexts": [
                "Iron for oxygen transport; Vitamin D for bone and muscle health.",
                "Magnesium, Zinc, and B vitamins aid energy and immune functions.",
            ],
        },
    ]

# ---------------------------------------------------------------------
# Collect RAG responses
# ---------------------------------------------------------------------
def get_rag_responses(evaluation_data):
    print("🚀 Initializing FitScience Coach RAG System for evaluation…")
    print("🔑 Using OpenAI API key for improved faithfulness")
    rag = FitScienceRAG(use_llama=True, openai_api_key=OPENAI_API_KEY)
    rag.initialize_system()
    results = []
    for i, q in enumerate(evaluation_data, 1):
        print(f"📝 Query {i}: {q['question']}")
        try:
            r = rag.query(q["question"])
            results.append({
                "question": q["question"],
                "answer": r["answer"],
                "contexts": q["contexts"],
                "ground_truth": q["ground_truth"],
            })
            print(f"✅ Answer {i} captured.")
        except Exception as e:
            print(f"❌ Query {i} failed: {e}")
            results.append({
                "question": q["question"],
                "answer": f"Error: {e}",
                "contexts": q["contexts"],
                "ground_truth": q["ground_truth"],
            })
    return results

# ---------------------------------------------------------------------
# RAGAS evaluation
# ---------------------------------------------------------------------
def run_ragas_evaluation():
    print("🔬 Starting RAGAs Evaluation for FitScience Coach…")
    print("🔑 Using OpenAI GPT-4o-mini (fast & reliable)")
    
    eval_data = create_evaluation_dataset()
    print(f"📊 Dataset contains {len(eval_data)} questions")
    responses = get_rag_responses(eval_data)

    dataset = Dataset.from_dict({
        "question": [r["question"] for r in responses],
        "answer": [r["answer"] for r in responses],
        "contexts": [r["contexts"] for r in responses],
        "ground_truth": [r["ground_truth"] for r in responses],
    })

    metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall(), ContextRelevance()]
    print("🎯 Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall, Context Relevance")

    # Initialize OpenAI models
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    print("✅ OpenAI models initialized")

    # Run evaluation
    try:
        print("⚙️ Running RAGAS evaluation with OpenAI…")
        result = evaluate(dataset, metrics=metrics, llm=llm, embeddings=embeddings)
        print("✅ Evaluation completed successfully!")
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None

    # Extract scores
    print("\n🎉 RAGAS Evaluation Results:")
    print("="*60)
    scores_dict = result._scores_dict
    for k, v in scores_dict.items():
        val = v[0]
        print(f"{k:22}: {val if not pd.isna(val) else 'NaN'}")

    vals = [v[0] for v in scores_dict.values() if not pd.isna(v[0])]
    overall = sum(vals)/len(vals) if vals else float("nan")
    print(f"\n🏁 Overall RAGAS Score: {overall:.3f}")

    out = {
        "metrics": {k: (v[0] if not pd.isna(v[0]) else None) for k, v in scores_dict.items()},
        "overall_score": overall,
        "details": {"system": "FitScience Coach v1.0", "model": "gpt-4o-mini", "questions": len(dataset)},
    }
    with open("ragas_results/ragas_evaluation_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("💾 Saved → ragas_results/ragas_evaluation_results.json")
    return out

# ---------------------------------------------------------------------
if __name__ == "__main__":
    res = run_ragas_evaluation()
    if res:
        print("\n📊 Summary")
        print("="*60)
        print(f"Overall Score: {res['overall_score']:.3f}")
        for k, v in res["metrics"].items():
            print(f"{k:22}: {v}")
    else:
        print("⚠️ RAGAS evaluation did not complete.")

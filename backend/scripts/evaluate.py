import json

from tradepilot.evaluation import evaluate_dataset

if __name__ == "__main__":
    print(json.dumps(evaluate_dataset("../data/evaluation/inquiries.json"), indent=2))

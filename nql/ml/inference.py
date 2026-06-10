import torch
from .model import get_tokenizer
import json
import os
import time
import argparse

class MLInference:
    def __init__(self, model_path="nql/ml/models/planner_v2.pt", mapping_path="nql/ml/data/mapping.json"):
        self.tokenizer = get_tokenizer()
        
        # Set quantization engine for compatibility
        import torch.backends.quantized
        if 'qnnpack' in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = 'qnnpack'
            
        self.model = torch.jit.load(model_path)
        self.model.eval()
        
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)
            self.actions = mapping['actions']
            self.operators = mapping.get('operators', ['=', '>', '<', 'NONE'])

    def predict(self, query):
        start_time = time.time()
        encoding = self.tokenizer(
            query,
            padding='max_length',
            truncation=True,
            max_length=128,
            return_tensors='pt'
        )
        
        with torch.no_grad():
            outputs = self.model(encoding['input_ids'], encoding['attention_mask'])
        
        action_idx = torch.argmax(outputs['action'], dim=1).item()
        operator_idx = torch.argmax(outputs['operator'], dim=1).item()
        
        confidence = torch.softmax(outputs['action'], dim=1)[0][action_idx].item()
        
        inference_time = (time.time() - start_time) * 1000 # ms
        
        return {
            "plan": {
                "action": self.actions[action_idx],
                "operator": self.operators[operator_idx],
                "has_filter": outputs['has_filter'].item() > 0.5,
                "has_sort": outputs['has_sort'].item() > 0.5,
                "has_limit": outputs['has_limit'].item() > 0.5,
            },
            "confidence": round(confidence, 4),
            "inference_time_ms": round(inference_time, 2)
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    args = parser.parse_args()
    
    inf = MLInference()
    result = inf.predict(args.query)
    print(json.dumps(result, indent=2))

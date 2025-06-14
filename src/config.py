models={
    "models": {
        "Gemini 2.5 Pro": "gemini-2.5-pro-preview-06-05",
        "Gemini 2.5 Flash": "gemini-2.5-flash-preview-05-20",
        "Gemini 2.0 Flash": "gemini-2.0-flash",
        "Gemini 1.5 Pro": "gemini-1.5-pro-002",
    },
    "defaults": {
        "extraction": "Gemini 2.5 Flash",
        "evaluation": "Gemini 2.5 Pro"
    }
}

# Parse the environment variable into a dictionary
models_dict = models["models"]
defaults = models["defaults"]
model_names = list(models_dict.keys())

# Get default indices safely (fallback to 0 if default not found)
default_extraction_idx = model_names.index(defaults["extraction"]) if defaults["extraction"] in model_names else 0
default_evaluation_idx = model_names.index(defaults["evaluation"]) if defaults["evaluation"] in model_names else 0
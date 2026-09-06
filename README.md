# Cognitive Architecture Playground

![Status](https://img.shields.io/badge/Status-Prototype-orange)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Tests](https://img.shields.io/badge/Tests-87%20Passing-green)

An experimental, dependency-light Python framework for making symbolic reasoning inspectable. It combines four modules that can also be used independently:

- **Working memory:** chunk storage, activation dynamics, decay and attention.
- **Metacognition:** confidence tracking, calibration, issue detection and reflection.
- **Causal reasoning:** directed graphs, d-separation, interventions and effect estimation.
- **Analogical reasoning:** structure mapping, retrieval and cross-domain inference.

The project is a research and teaching playground. It is not a medical, financial or autonomous decision-making system; examples are demonstrations of the algorithms, not recommendations.

## Project structure

```text
cognitive_arch/
├── core/                  # Shared types and the integration layer
├── modules/
│   ├── working_memory/    # Chunks, attention and activation
│   ├── metacognition/     # Confidence, monitoring and reflection
│   ├── causal/            # Graphs, inference and interventions
│   └── analogical/        # Structures, retrieval and mapping
└── examples/              # Runnable demonstrations
```

## Quick start

The package uses only the Python standard library.

```bash
git clone https://github.com/mariuscomper/Cognitive-Architecture-Playground.git
cd Cognitive-Architecture-Playground

# Run the test suite
python3 -m unittest discover -s tests -v

# Run the integrated demonstration
python3 -m cognitive_arch.examples.demo_integrated
```

For an editable local installation:

```bash
python3 -m pip install -e .
```

## Small example

```python
from cognitive_arch.core.architecture import CognitiveArchitecture

agent = CognitiveArchitecture()
agent.remember("The sky is blue")
agent.remember("It is raining")

for memory in agent.recall("sky"):
    print(memory["content"], memory["activation"])
```

## Testing

The repository currently contains 87 unit tests covering the four modules and their integration points. GitHub Actions runs the suite on every push and pull request to `main`.

## Limitations

- The framework is symbolic and does not use a language model.
- The analogical mapper is greedy and can miss an optimal mapping in complex structures.
- Confidence values are recorded estimates; they are not calibrated probabilities until outcomes are supplied.
- The current implementation does not learn weights or policies from experience.

## Status

This is a prototype intended for experiments, tests and extension. The Python architecture is the source of truth; presentation files from an unrelated Stoicism project are intentionally not part of this repository.

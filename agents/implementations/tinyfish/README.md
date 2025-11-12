# TinyFish Agent

This directory contains the TinyFish custom agent implementation for the Web Agent Arena.

## Overview

The TinyFish agent is a custom web navigation agent with specialized capabilities for:
- Complex multi-step web tasks
- Advanced reasoning and planning
- Efficient browser control
- Robust error handling

## Implementation Status

🚧 **Under Development**

## Architecture

The TinyFish agent follows the standard `BaseAgent` interface but includes custom logic for:
- Task decomposition
- Tool selection and execution
- State management
- Output formatting

## API Integration

The agent communicates with the TinyFish API endpoint at:
```
https://api.tinyfish.ai/v1/agent
```

API key is required and should be set in the environment variables or Streamlit secrets.

## Usage

The agent is automatically registered in the agent registry and can be selected from the arena dropdown.

## Development

To add custom logic to the TinyFish agent:

1. Edit `agent.py` with your implementation
2. Add any helper modules as needed
3. Update tests in the tests directory
4. Document any special capabilities or requirements

## Links

- [Arena Interface](https://your-arena-url.streamlit.app)
- [TinyFish API Documentation](https://docs.tinyfish.ai)
- [GitHub Repository](https://github.com/your-org/tinyfish-agent)


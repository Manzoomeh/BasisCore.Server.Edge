# BasisEdge

**BasisEdge** is designed to enable edge network communications for software applications that must connect to various data centers or multiple service providers simultaneously. Developed by **Monzoomeh Negaran**'s engineers, the project is open-source, making it possible for anyone to contribute to development or optimization. Through the application of AI assistants and the broader **Basis** framework, it takes only minutes to develop new tools using BasisEdge—one of the most valuable features of this framework.

## Why BasisEdge?

Most current network-oriented applications are prone to require stable and secure connections between different data centers and services. **BasisEdge** fills such needs by positioning itself in the network edge. It offers features such as:

- **Easy API Construction**: Create APIs in no time to facilitate multiple systems in exchange and sharing information.

- **Multi-Data-Center Connection**: Interact with numerous data centers or providers simultaneously easily.
- **Security and Reliability**: Emphasize security without sacrificing the reliability required for modern services.
- **Open Source**: The source code is open, allowing you to modify and extend it to fit your specific application.

## Key Features

- **Flexible Dispatching**: Makes support for various communication protocols (HTTP, WebSockets, named pipes, etc.) available to support varying application requirements.

- **Flexible Contexts**: Offers context-aware request handling for RESTful APIs, WebSockets, data sources, and message queues.
- **Declarative Routing**: Has a stunning predicate system for defining routes and request filters in minimal code.
- **Rich Database Support**: SQL Server, SQLite, MongoDB, RESTful APIs, RabbitMQ, and more out of the box.
- **Effective Caching**: Memory caching with decorator support and signal-based invalidation.
- **Rich Logging**: Schema-based logging options with multiple output targets.
- **Middleware Features**: Makes it easy to handle HTTP headers, CORS, and error handling.

## Example Usage

Here is a simple example in Python illustrating how to create a basic RESTful endpoint with BasisEdge:

```python
from bclib import edge

# Create application
options = {
    "server": "localhost:8080",
    "router": "restful"
}
app = edge.from_options(options)

# Create a RESTful endpoint
@app.restful_action(app.url("api/data"))
def process_data(context: edge.RESTfulContext):
    return {"message": "Hello from BasisCore Edge!"}

# Start server
app.listening()
```
In just a few lines of code, you have a functioning endpoint that responds with a JSON message. This illustrates how simple it is to begin using **BasisEdge**.

## Use Cases

**BasisEdge** is ideal for:

- Creating modern web APIs and microservices
- Creating data integration gateways
- Creating real-time web applications
- Integrating many different systems through an efficient communication layer
- Serving as a backend for projects using **BasisCore** frontend libraries

## Installation

You can install **BasisEdge** (or the `bclib` package it belongs to) with pip:

```bash
pip install bclib
```

Once installed, read the documentation or inspect the source code to determine how to get **BasisEdge** working for your purposes.

## Contributions

Since **BasisEdge** is open source, we encourage contributions from anyone. If you'd like to add new features, enhance performance, or squelch bugs, your contributions make this framework better for everyone.

1. **Fork** the repository.
2. Create a new **branch** for your fix or feature.
3. Create a **pull request** to merge your changes into the main branch.

We appreciate all feedback and are excited to collaborate and work together to continuously improve **BasisEdge**.

## Contact Us

For any feedback, collaborations, or proposals, feel free to contact the **Monzoomeh Negaran** team. We look forward to hearing from you:

- **Email**: [info@monzoomeh.com](mailto:info@monzoomeh.com)  
- **Website**: [https://monzoomeh.com](https://monzoomeh.com)

Thank you for your interest in **BasisEdge**. We wish it to be a strong and secure platform for your network-related activities! In case of questions, feel free to contact us.

---

*© 2025 Monzoomeh Negaran. All Rights Reserved.*

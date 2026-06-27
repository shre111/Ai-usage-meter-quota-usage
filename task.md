# AI Usage Metering and Quota Service

**Submission deadline:** Monday, June 29, 2026, by 9:00 PM IST

**AI tools:** Allowed and expected. We evaluate how you understand the problem, how you solve it, how you define and interpret metrics, how you make tradeoffs, and how clearly you explain the solution in your walkthrough. We are not grading syntax recall though proper use of Pythonic ways to write code will be evaluated.

## Overview

Build a small Python service that exposes an AI-powered text generation API and tracks usage against configurable per-user credit limits.

The assignment is intended to evaluate backend engineering judgment in a realistic AI application setting. Your solution should show how you think about service boundaries, request handling, usage accounting, configurability, and failure behavior.

## Scenario

You are building the usage-control layer for an AI product. Users can submit prompts to a generation endpoint and receive responses from an AI model. Each request consumes credits based on the usage reported by the AI layer.

Different users may have different commercial arrangements. One user may have a low monthly allowance and a standard credit multiplier. Another user may have a higher allowance but a different multiplier. The service must account for these differences when deciding whether a request is allowed and when recording usage.

The AI implementation can be backed by a real LLM provider or by a mocked/local implementation. A mocked implementation is acceptable as long as it returns realistic usage information and makes the metering behavior easy to demonstrate.

## Core Requirements

Build a FastAPI application that supports the following capabilities:

- Submit a text generation request for a user.
- Return a generated response from either a mocked or real AI generation layer.
- Track raw usage from the AI layer, such as prompt tokens, completion tokens, total tokens, or another clearly explained unit.
- Convert raw usage into billable credits using a multiplier configured for that user.
- Enforce a quota or credit allowance configured for that user.
- Support different quota settings for different users.
- Support different credit multipliers for different users.
- Expose a way to inspect a user's current usage, remaining allowance, and relevant configuration.
- Record enough usage history to explain how credits were consumed over time.
- Return clear API behavior when a user is at or over their quota.

The storage layer can be in-memory, file-backed, SQLite, Postgres, or another reasonable option. Your design document should explain the tradeoff you chose.

## Expected API Capabilities

The exact API shape is up to you, but the service should make these workflows possible:

- Configure or update a user's quota settings.
- Configure or update a user's credit multiplier.
- Generate text for a specific user.
- Retrieve the user's current usage and remaining credits.
- Inspect usage records for a user.

The API responses should be clear enough for a client application to understand whether a request succeeded, failed because of quota, or failed because of another service error.

## Usage and Credit Behavior

Your solution should define how raw AI usage maps to credits. For example, a service may choose to base credits on total tokens, separate input/output units, or another usage metric. The important requirement is that the rule is explicit, deterministic, and affected by the user's configured multiplier.

The service should also define what happens when a request interacts with quota boundaries, including:

- The user has no quota configuration.
- The user has already exhausted their quota.
- The request would consume more credits than the user has remaining.
- The request succeeds and usage is reported.
- The AI generation fails before usage is available.
- The AI generation fails after partial usage may have occurred.
- The user's multiplier changes after earlier usage records already exist.

You do not need to support every possible edge case in code, but the behavior you choose should be intentional and explained.

## Consistency Challenge

In most AI systems, the exact usage is not known until after generation finishes. Your service should therefore account for the difference between the usage estimate available before a request starts and the actual usage reported after the AI layer completes.

Your design and implementation should make the behavior clear when:

- A request appears affordable before generation but actual usage is higher than expected.
- A request is rejected because its estimated usage would exceed the remaining quota.
- Two or more requests for the same user are submitted close together.
- A user's quota or multiplier is updated while requests or historical usage records exist.

This section is intentionally important. Treat it as part of the product behavior, not as an optional extension.

## Design Expectations

Structure the project as a maintainable Python service rather than a single script.

We are interested in how you separate responsibilities across the system, especially around:

- API routing and request validation.
- User-level configuration.
- AI generation.
- Usage calculation.
- Quota enforcement.
- Usage recording.
- Error handling.
- Testability.

The design should make it possible to reason about future changes, such as:

- Adding more AI endpoints.
- Changing the AI provider.
- Moving from local storage to a real database.
- Introducing different quota periods or plans.
- Auditing usage for billing or customer support.

Your design document should also explain the quota behavior using at least one concrete numerical example. For example, describe one user with a quota, multiplier, current usage, estimated request size, and actual request size. Show the resulting decision and final recorded usage.

The example should match the behavior of your implementation and Loom demo.

Avoid overbuilding. A focused solution with clear tradeoffs is preferred over a broad solution that is hard to understand or run.

## Testing Requirements

Include tests that demonstrate the core behavior of the service.

At minimum, tests should cover:

- Successful generation and usage recording.
- Credit calculation using a per-user multiplier.
- Different users receiving different quota or multiplier behavior.
- Quota enforcement when a user has enough remaining credits.
- Quota-exceeded behavior when a user does not have enough remaining credits.
- Behavior when the AI generation layer fails.
- Retrieval of current usage and remaining allowance.
- Behavior when actual usage differs from the pre-request estimate.
- Behavior for near-simultaneous requests from the same user.

Tests should be runnable with a simple command documented in the README.

## Submission Requirements

Submit the following:

1. **Solution design document**

This can be a Google Doc, Markdown file, or similar. It should explain your architecture, major tradeoffs, API behavior, quota model, credit calculation model, persistence choice, failure-handling choices, and at least one concrete quota scenario.

1. **GitHub repository**

Include the full implementation, setup instructions, environment requirements, and test instructions.

1. **Video walkthrough**

Record a short walkthrough showing the service in action. This can be brief, but it should demonstrate successful generation, usage tracking, and quota enforcement. This can be shared through Jam.dev/Loom or any equivalent platform.

## Evaluation Criteria

Submissions will be evaluated on:

- Clear Python package structure.
- Clean FastAPI API design.
- Thoughtful separation of service responsibilities.
- Correct per-user quota behavior.
- Correct per-user credit multiplier behavior.
- Sensible usage metering and credit accounting.
- Clear behavior when quota is reached or exceeded.
- Practical failure handling around the AI layer.
- Reasonable handling of estimated usage versus actual usage.
- Awareness of consistency issues for concurrent requests.
- Whether the design explanation matches the implementation.
- Ability to explain tradeoffs in the Loom walkthrough.
- Useful tests for important behavior.
- Clarity of the solution design document.
- Ease of running and reviewing the project.

We value pragmatic, well-explained solutions over unnecessarily complex ones.
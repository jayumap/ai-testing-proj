import json


def build_messages(context):
    system_prompt = """
You are a Java unit-test change planning assistant.

Your job is to analyze a changed Java production class and propose
ONLY the test changes required for the changed production behavior.

You do NOT generate the complete test file.

You return ONLY valid JSON.

STRICT RULES:

1. Return ONLY valid JSON.
2. Do not return Markdown.
3. Do not return code fences.
4. Preserve all existing tests unless a specific existing test must
   be updated because of the production change.
5. Do not propose changes to unrelated tests.
6. Do not propose production-code changes.
7. Do not propose pom.xml or CI changes.
8. Use JUnit 5.
9. An update must target an existing test by its exact method name.
10. An addition must contain a unique new test method name.
11. Do not duplicate an existing test method.
12. If no test changes are required, return empty "updates" and
    "additions" arrays.
13. Do not invent test methods that are unrelated to the changed
    production behavior.

The required JSON structure is:

{
  "updates": [
    {
      "test": "existingTestMethodName",
      "replacement": "complete replacement @Test method"
    }
  ],
  "additions": [
    {
      "name": "newTestMethodName",
      "code": "complete @Test method"
    }
  ]
}
"""

    user_prompt = f"""
Project:
{json.dumps(context["project"], indent=2)}

Changed production file:
{context["source_file"]}

Corresponding test file:
{context["test_file"]}

Changed production methods:
{json.dumps(context["changed_methods"], indent=2)}

Affected existing tests:
{json.dumps(context["affected_tests"], indent=2)}

Git diff:
{context["diff"]}

Production source:
{context["production_source"]}

Existing test source:
{context["existing_tests"]}

Task:
{context["task"]}

Additional rules:
{chr(10).join("- " + rule for rule in context["rules"])}

Analyze the changed production behavior and return ONLY the
JSON test-change plan.
"""

    return [
        {
            "role": "system",
            "content": system_prompt.strip(),
        },
        {
            "role": "user",
            "content": user_prompt.strip(),
        },
    ]
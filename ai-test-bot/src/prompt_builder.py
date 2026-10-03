def build_messages(context):
    system_prompt = """
You are a Java unit-test generation assistant.

Your job is to generate or update the JUnit 5 test file corresponding
to a changed Java production class.

STRICT RULES:

1. Return ONLY the complete Java test file.
2. Do not return Markdown code fences.
3. Preserve all existing tests unless they are directly invalidated
   by the production change.
4. Add tests for the changed behavior.
5. Use JUnit 5.
6. Follow the style of the existing test class.
7. Do not modify production code.
8. Do not modify pom.xml, CI configuration, or any other file.
9. The output must be compilable Java source code.
10. Return the COMPLETE test file, not a patch or partial snippet.
"""

    user_prompt = f"""
Project:
{context["project"]}

Changed production file:
{context["source_file"]}

Corresponding test file:
{context["test_file"]}

Git diff:
```text
{context["diff"]}
```

Production source:

```
{context["production_source"]}
```

Existing test source:

```
{context["existing_tests"]}
```

Task:
{context["task"]}

Additional rules:
{chr(10).join("- " + rule for rule in context["rules"])}

Generate the complete updated test file now.
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
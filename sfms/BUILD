poetry_requirements(
    name="poetry",
)

pex_binary(
    entry_point="sfms.py",
)

python_sources(
    name="sfms0",
    interpreter_constraints=["==2.7.*"]
)

pex_binary(
    name="sfms_local",
    entry_point="sfms_local.py",
)

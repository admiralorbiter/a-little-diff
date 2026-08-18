"""Synthetic MOOSEDev N-Quads test fixtures."""

# Base State (A): Manual attendance constraint + dependent decision + requirement
NQUADS_STATE_A = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <http://purl.org/dc/terms/title> "Teacher attendance constraint" .
<urn:record:constraint:1> <http://purl.org/dc/terms/description> "Teacher attendance must be entered manually." .
<urn:record:constraint:1> <https://moosedev.org/ontology/status> "active" .

<urn:record:decision:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:decision:1> <http://purl.org/dc/terms/title> "Manual attendance workflow" .
<urn:record:decision:1> <http://purl.org/dc/terms/description> "Build a manual entry screen for teachers to submit attendance daily." .
<urn:record:decision:1> <https://moosedev.org/ontology/status> "active" .
<urn:record:decision:1> <https://moosedev.org/ontology/isMotivatedBy> <urn:record:constraint:1> .

<urn:record:requirement:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:record:requirement:1> <http://purl.org/dc/terms/title> "Teacher dashboard" .
<urn:record:requirement:1> <http://purl.org/dc/terms/description> "Dashboard summarizing weekly attendance." .
<urn:record:requirement:1> <https://moosedev.org/ontology/status> "active" .
<urn:record:requirement:1> <https://moosedev.org/ontology/concerns> <urn:record:decision:1> .
""".strip()


# Head State (B): Constraint C1 superseded by Constraint C2 (external integration)
NQUADS_STATE_B = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <http://purl.org/dc/terms/title> "Teacher attendance constraint" .
<urn:record:constraint:1> <http://purl.org/dc/terms/description> "Teacher attendance must be entered manually." .
<urn:record:constraint:1> <https://moosedev.org/ontology/status> "superseded" .

<urn:record:constraint:2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:2> <http://purl.org/dc/terms/title> "Pathful attendance import" .
<urn:record:constraint:2> <http://purl.org/dc/terms/description> "Pathful provides teacher attendance through its import." .
<urn:record:constraint:2> <https://moosedev.org/ontology/status> "active" .
<urn:record:constraint:2> <https://moosedev.org/ontology/supersedes> <urn:record:constraint:1> .

<urn:record:decision:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:decision:1> <http://purl.org/dc/terms/title> "Manual attendance workflow" .
<urn:record:decision:1> <http://purl.org/dc/terms/description> "Build a manual entry screen for teachers to submit attendance daily." .
<urn:record:decision:1> <https://moosedev.org/ontology/status> "active" .
<urn:record:decision:1> <https://moosedev.org/ontology/isMotivatedBy> <urn:record:constraint:1> .

<urn:record:requirement:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:record:requirement:1> <http://purl.org/dc/terms/title> "Teacher dashboard" .
<urn:record:requirement:1> <http://purl.org/dc/terms/description> "Dashboard summarizing weekly attendance." .
<urn:record:requirement:1> <https://moosedev.org/ontology/status> "active" .
<urn:record:requirement:1> <https://moosedev.org/ontology/concerns> <urn:record:decision:1> .
""".strip()

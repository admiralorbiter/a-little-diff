"""Synthetic MOOSEDev N-Quads test fixtures."""

# Base State (A): Manual attendance constraint + dependent decision + requirement using real MOOSEDev vocabulary
NQUADS_STATE_A = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasTitle> "Teacher attendance constraint" .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasDescription> "Teacher attendance must be entered manually." .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .

<urn:record:decision:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:decision:1> <https://moosedev.org/ontology/hasTitle> "Manual attendance workflow" .
<urn:record:decision:1> <https://moosedev.org/ontology/hasDescription> "Build a manual entry screen for teachers to submit attendance daily." .
<urn:record:decision:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:record:decision:1> <https://moosedev.org/ontology/isMotivatedBy> <urn:record:constraint:1> .

<urn:record:requirement:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasTitle> "Teacher dashboard" .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasDescription> "Dashboard summarizing weekly attendance." .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:record:requirement:1> <https://moosedev.org/ontology/concerns> <urn:record:decision:1> .
""".strip()


# Head State (B): Constraint C1 superseded by Constraint C2 with separate Rationale record and isSupersededBy inverse
NQUADS_STATE_B = """
<urn:record:constraint:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasTitle> "Teacher attendance constraint" .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasDescription> "Teacher attendance must be entered manually." .
<urn:record:constraint:1> <https://moosedev.org/ontology/hasLifecycleStatus> "superseded" .
<urn:record:constraint:1> <https://moosedev.org/ontology/isSupersededBy> <urn:record:constraint:2> .

<urn:record:constraint:2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Constraint> .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasTitle> "Pathful attendance import" .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasDescription> "Pathful provides teacher attendance through its import." .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:record:constraint:2> <https://moosedev.org/ontology/supersedes> <urn:record:constraint:1> .
<urn:record:constraint:2> <https://moosedev.org/ontology/hasRationale> <urn:record:rationale:1> .

<urn:record:rationale:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Rationale> .
<urn:record:rationale:1> <https://moosedev.org/ontology/hasTitle> "Pathful integration rationale" .
<urn:record:rationale:1> <https://moosedev.org/ontology/hasDescription> "Vendor released attendance endpoint." .
<urn:record:rationale:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .

<urn:record:decision:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Decision> .
<urn:record:decision:1> <https://moosedev.org/ontology/hasTitle> "Manual attendance workflow" .
<urn:record:decision:1> <https://moosedev.org/ontology/hasDescription> "Build a manual entry screen for teachers to submit attendance daily." .
<urn:record:decision:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:record:decision:1> <https://moosedev.org/ontology/isMotivatedBy> <urn:record:constraint:1> .

<urn:record:requirement:1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://moosedev.org/ontology/Requirement> .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasTitle> "Teacher dashboard" .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasDescription> "Dashboard summarizing weekly attendance." .
<urn:record:requirement:1> <https://moosedev.org/ontology/hasLifecycleStatus> "accepted" .
<urn:record:requirement:1> <https://moosedev.org/ontology/concerns> <urn:record:decision:1> .
""".strip()

# Einstieg

Die **AI Museum Pipeline** ist selbst gehostete Middleware für multimodale
Anreicherung von Museumssammlungen. Sie sitzt zwischen einer bestehenden
Sammlungsdatenbank und neuen Such-, Erschließungs- oder Forschungsanwendungen.

Sie ersetzt nicht das primäre Dokumentationssystem des Museums. Quelldaten
und maschinell generierte Anreicherung bleiben getrennt.

## Was sie erzeugt

- SigLIP2- und DINOv3-Bild-Embeddings;
- BGE-M3-Text-Embeddings;
- konsolidierte Bildbeschreibungen;
- generierte, auditierte und reparierte Schlagwörter;
- optionalen GND-Normdatenabgleich;
- optionale kontrollierte Wirkungslesarten (Machine Heart);
- optionale institutionell definierte Themenbeziehungen.

## Wo finde ich was?

Die Dokumentation ist entlang zweier Achsen organisiert: **wie tief** du
einsteigen willst (Einsteiger → Profi) und **welche Seite** dich
interessiert (museologisch/fachlich oder technisch/Infrastruktur). Die
meisten Themen gibt es auf beiden Seiten — z. B. erklärt `WORKFLOW.md` pro
Pipeline-Schritt sowohl die museologische Idee als auch die technische
Umsetzung.

|  | Museologisch / fachlich | Technisch / Infrastruktur |
| --- | --- | --- |
| **Einsteiger** — was ist das, kann ich es nutzen? | [`MUSEOLOGICAL_PRINCIPLES.md`](MUSEOLOGICAL_PRINCIPLES.md) — die 12 interpretativen Leitplanken | [README](../README.md) — Kurzüberblick, Quick Start |
| **Intermediate** — ich richte es für mein Museum ein | [`WORKFLOW.md`](WORKFLOW.md) — was passiert mit einem Objekt, Schritt für Schritt | [`PROFILES.md`](PROFILES.md) — die fünf Profiltypen, eigenes Museum einrichten |
| **Profi** — ich will die strategischen Prinzipien hinter jeder Regel verstehen bzw. tief in Infrastruktur/Deployment gehen | [`MUSEUM_DESIGN_DECISIONS.md`](MUSEUM_DESIGN_DECISIONS.md) — warum 11 Cluster, warum Audit/Judge getrennt sind, Farblogik im Detail · [`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) — eigene Themen-Wissensbasis aufbauen · [`EMOTION_METHOD.md`](EMOTION_METHOD.md) — Machine Heart ersetzen/erweitern | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) — Konfigurationsmodell + Infra-Topologie · [`INSTALLER.md`](INSTALLER.md) · [`MANUAL_DEPLOYMENT.md`](MANUAL_DEPLOYMENT.md) · [`FRESH_HOST_CHECKLIST.md`](FRESH_HOST_CHECKLIST.md) · [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) |

Weitere Referenzen ohne festen Platz in der Matrix:
[`ROADMAP.md`](ROADMAP.md) (was als Nächstes ansteht),
[`../infra/cpu/INSTALL.md`](../infra/cpu/INSTALL.md),
[`../infra/gpu/INSTALL.md`](../infra/gpu/INSTALL.md).

Das kalibrierte H100-Deployment ist dokumentiert unter
`infra/gpu/stadtmuseum-berlin/h100-80gb/`. Es ist eine getestete
Referenzkonfiguration, keine Voraussetzung für die Nutzung der Pipeline —
generische Deployments starten bei `infra/gpu/generic/`.

## Wenn du mit Sammlungen oder kuratorischen Daten arbeitest

1. [`WORKFLOW.md`](WORKFLOW.md) — was passiert mit einem Objekt?
2. [`MUSEOLOGICAL_PRINCIPLES.md`](MUSEOLOGICAL_PRINCIPLES.md) — wo liegen die interpretativen Grenzen?
3. [`PROFILES.md`](PROFILES.md) — was muss ein anderes Museum konfigurieren?
4. [`EMOTION_METHOD.md`](EMOTION_METHOD.md) — mitgelieferter Machine-Heart-Default und eigener Vokabular-/DB-Vertrag.
5. [`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) — wie die getestete institutionelle Themen-Wissensbasis strukturiert ist.
6. [`MUSEUM_DESIGN_DECISIONS.md`](MUSEUM_DESIGN_DECISIONS.md) — warum die 11 Schlagwortcluster, Prompt-/Audit-Design, Farbschichten und der Topics-Vertrag so aufgebaut sind.

## Wenn du mit Infrastruktur arbeitest

1. [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md)
2. [`INSTALLER.md`](INSTALLER.md)
3. [`MANUAL_DEPLOYMENT.md`](MANUAL_DEPLOYMENT.md)
4. [`FRESH_HOST_CHECKLIST.md`](FRESH_HOST_CHECKLIST.md)
5. [`../infra/cpu/INSTALL.md`](../infra/cpu/INSTALL.md)
6. [`../infra/gpu/INSTALL.md`](../infra/gpu/INSTALL.md)

# Mitwirken

Danke für Interesse an AI Museum Pipeline. Dieses Dokument beschreibt, wie
Änderungen vorgeschlagen werden und welche Erwartungen an Pull Requests
bestehen.

## Bevor du größere Änderungen beginnst

Für alles über kleine Fixes hinaus (neue Module, geänderte Schemas,
architektonische Entscheidungen) bitte zuerst ein Issue öffnen und kurz
beschreiben, was und warum. Das verhindert doppelte Arbeit und stellt
sicher, dass eine Änderung zur bestehenden Architektur passt — siehe dazu
[`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md) und
[`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md) für die
Prinzipien, an denen sich museumsfachliche Änderungen orientieren sollten.

## Grundregeln

- **Der Python-Core bleibt museumsagnostisch.** Keine Institutionsnamen,
  keine realen URLs, keine festen Pfade zu einem bestimmten Museumsprofil
  unter `src/museum_pipeline/`. Institutionsspezifisches gehört nach
  `profiles/<museum>/`. Der Test
  `tests/test_structure.py::test_no_institution_semantics_in_src` prüft
  einen Teil davon automatisiert, ersetzt aber keine manuelle Prüfung.
- **Keine geheimen Themenschwerpunkte.** `profiles/stadtmuseum-berlin/`
  enthält bewusst keine institutionelle Topics-Wissensbasis. Pull Requests
  dürfen keine echten Themennamen, Taxonomien oder Framework-Inhalte
  hinzufügen — weder dort noch in `profiles/_template/`.
- **Keine Secrets.** Keine echten Zugangsdaten, Tokens, privaten
  Server-URLs oder IP-Adressen aus produktiven Deployments committen. Für
  Beispiele reservierte Testadressen nutzen (`203.0.113.0/24`,
  `192.0.2.0/24` nach RFC 5737) und `example.org`/`example.com` als
  Platzhalter-Domains.
- **Synthetische Fixtures statt echter Objektdaten.** Für Tests, Beispiele
  und Bugreports `DEMO-001`-artige Bezeichner statt echter
  Inventarnummern verwenden.

## Entwicklungsumgebung einrichten

```bash
git clone https://github.com/sebastianruffberlin/AI-Museum-Pipeline.git
cd AI-Museum-Pipeline
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

## Vor jedem Pull Request

```bash
.venv/bin/python -m compileall -q src services tools tests
.venv/bin/ruff check src tests services tools
.venv/bin/python -m pytest -q
```

Alle drei müssen fehlerfrei durchlaufen; dieselben Prüfungen laufen auch in
der CI (`.github/workflows/ci.yml`). Zusätzlich prüft die CI
`pip-audit` für Root- sowie Embedding-/Presign-Service-Dependencies, die
Docker-Compose-Konfigurationen und scannt mit Gitleaks nach committeten
Secrets.

`ruff` ist hier bewusst nur auf echte Fehler (`F`-Regeln: unbenutzte
Importe, undefinierte Namen usw.) konfiguriert, siehe `[tool.ruff.lint]` in
`pyproject.toml`. Der bestehende Code nutzt durchgängig kompakte
Einzeiler-Anweisungen; das ist bewusster Stil, kein Lint-Fehler.

## Tests

- Neue Funktionalität braucht einen Test.
- Ein behobener Fehler (insbesondere sicherheitsrelevante Fixes) sollte
  einen Regressionstest bekommen, der ohne den Fix fehlschlägt.
- Tests, die eine echte PostgreSQL-Verbindung brauchen, sind die Ausnahme,
  nicht die Regel — die meisten Contract-Tests laufen ohne laufende
  Datenbank.

## Dokumentation

Die Dokumentation ist auf Deutsch (siehe README, Abschnitt "Sprachhinweis").
Bei inhaltlichen Änderungen an Modulen, Prompts oder der Architektur bitte
die passende Datei unter `docs/` mit aktualisieren — insbesondere
`docs/MUSEUM_DESIGN_DECISIONS.md`, wenn sich eine museumsfachliche
Begründung ändert, oder `docs/SYSTEM_ARCHITECTURE.md`, wenn sich etwas an
Konfigurationsmodell oder Infrastruktur ändert. `docs/START_HERE.md` ist
der zentrale Einstiegspunkt und sollte bei neuen Dokumenten verlinkt
werden.

## Sicherheitslücken

Sicherheitslücken bitte **nicht** über ein öffentliches Issue melden —
siehe [`SECURITY.md`](SECURITY.md) für den privaten Meldeweg.

## Lizenz

Mit einem Beitrag stimmst du zu, dass dein Code unter der
[MIT-Lizenz](LICENSE) dieses Projekts veröffentlicht wird.

# Security Policy

## Sicherheitslücke melden

Bitte **kein** öffentliches Issue mit Zugangsdaten, privaten Museumsdaten,
Infrastrukturdetails oder einer ausnutzbaren Sicherheitslücke öffnen.

GitHub Private Vulnerability Reporting nutzen, wenn für das öffentliche
Repository aktiviert. Ist dieser Kanal nicht verfügbar, die Maintainer über
einen privaten Kanal kontaktieren, der auf deren GitHub-Profilen gelistet
ist, und um einen privaten Sicherheitskontakt bitten. Meldungen auf Deutsch
oder Englisch sind willkommen.

Bei einer Meldung bitte angeben:

- betroffener Commit oder betroffenes Release;
- betroffene Komponente;
- reproduzierbare Schritte;
- erwartete Auswirkung;
- ob möglicherweise Zugangsdaten oder personen-/institutionsbezogene Daten
  offengelegt wurden.

## Secrets

Echte Secrets dürfen niemals committet werden. Laufzeit-Zugangsdaten
gehören in `.env` oder installer-generierte Dateien unter
`.museum-pipeline/` bzw. das externe GPU-Config-Verzeichnis.
Beispieldateien enthalten nur Platzhalter.

Wird trotzdem einmal ein Secret committet, reicht es nicht, nur die
aktuelle Datei zu entfernen: die Zugangsdaten rotieren und die Git-Historie
als kompromittiert behandeln.

## Unterstütztes Release

Sicherheitsfixes zielen auf die aktuelle öffentliche Release-Linie. Das
Referenzdeployment nutzt gepinnte/dokumentierte Komponentenversionen für
Reproduzierbarkeit, aber Nutzer bleiben selbst verantwortlich für
Sicherheitsupdates im eigenen Betriebssystem, Container und
Modell-Serving-Umfeld.

## SSH-Host-Key-Verifikation im GPU-Installer

Der Managed-GPU-Installer nutzt standardmäßig
`StrictHostKeyChecking=accept-new` (Trust-on-first-use). Für gehärtete
Deployments kann der Host-Key vorab außerhalb dieses Kanals verifiziert und
über `SSH_STRICT_HOST_KEY_CHECKING=yes` + `SSH_KNOWN_HOSTS_FILE` gepinnt
werden. Siehe [`docs/INSTALLER.md`](docs/INSTALLER.md), Abschnitt
"SSH-Host-Key-Verifikation".

## Embedding-Service und externe Bild-URLs

Lädt ein Museumsprofil Assets per `image_url` statt aus privatem S3, stellt
der Embedding-Service selbst einen HTTP-Request auf eine aus den
Objektdaten stammende URL. Der Service ist dagegen gehärtet: Schema-
Whitelist (nur `http`/`https`), DNS-Auflösung gegen private/loopback/
link-local/reservierte Adressbereiche gesperrt, jeder Redirect wird erneut
geprüft, Downloadgröße und Pixelzahl sind begrenzt
(`IMG_MAX_DOWNLOAD_BYTES`, `IMG_MAX_PIXELS`). Museen mit einem tatsächlich
privat liegenden Bildserver können einzelne Hosts über
`IMG_ALLOWED_PRIVATE_HOSTS` explizit freischalten — nur setzen, wenn dieser
Server wirklich intern liegt und vertrauenswürdig ist.

## Docker-Build-Context

`deploy/Dockerfile` nutzt `COPY . /app`. `.dockerignore` schließt `.env`,
`deployment.yaml`, generierte Secret-Dateien und Caches vom Build-Context
aus. Vor eigenen Docker-Builds sicherstellen, dass `.dockerignore` nicht
versehentlich entfernt oder eingeschränkt wurde, insbesondere wenn eine
echte `.env` im selben Verzeichnis liegt.

## Museumsdaten, Tracing und Verbose-Logs

Objektmetadaten, Prompts und Modellausgaben können unveröffentlichte
Sammlungsinformationen, personenbezogene Daten oder anderes
institutionssensibles Material enthalten.

- Phoenix-/OpenTelemetry-Tracing ist **standardmäßig deaktiviert**.
  Aktiviert, zeichnen LLM-Spans gekürzten Prompt-/Ausgabetext plus
  Objekt-IDs und Phasenmetadaten auf. Das Tracing-Backend als System
  behandeln, das Museumsdaten empfangen kann.
- `-v` und `-vv` geben bewusst vollständige Prompts/Modellantworten bzw.
  Zwischenstrukturen in der Konsole aus. Kein Verbose-Logging in einem
  geteilten Terminal, CI-Log oder zentralen Log-Collector nutzen, sofern
  dieses Datenziel nicht für die verarbeiteten Sammlungsdaten freigegeben
  ist.
- Keine Produktions-Objektdaten in öffentlichen Bugreports oder
  Reproduzierbarkeits-Beispielen verwenden; stattdessen synthetische
  Fixtures wie `DEMO-001` nutzen.

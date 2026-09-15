from pathlib import Path

FILES=[Path('index.html'),Path('egen-master-deck.html')]

for path in FILES:
    s=path.read_text()

    # Offline parser title: Client - Event Type - Location
    old="""  // --- title ---\n  const titleParts = [found['Event type'] || template.label];\n  if(paxNumber) titleParts.push(`${paxNumber} pax`);\n  if(locationDisplay) titleParts.push(`at ${locationDisplay}`);\n  const title = titleParts.join(' — ');"""
    new="""  // --- title: Client Name - Event Type - Location ---\n  const title = [\n    found['Client'] || 'Client TBC',\n    found['Event type'] || template.label,\n    locationDisplay || 'Location TBC'\n  ].join(' - ');"""
    if old in s:
        s=s.replace(old,new,1)

    # AI parser title: same standard using structured fields.
    old="title: parsed.title || parsed.eventTypeLabel || 'Untitled brief',"
    new="title: [parsed.companyClient || 'Client TBC', parsed.eventTypeLabel || 'Event', parsed.venue || 'Location TBC'].join(' - '),"
    s=s.replace(old,new,1)

    # Existing records in Master View: derive standardized display title from stored points.
    if 'function masterDisplayTitle(' not in s:
        anchor='function masterBriefType(b){'
        helper="""function briefPointValue(b, label){\n  const p=(b.points||[]).find(x=>x.label===label);\n  return p && p.value ? String(p.value).trim() : '';\n}\nfunction masterDisplayTitle(b){\n  const client=briefPointValue(b,'Company / Client');\n  const eventType=briefPointValue(b,'Event type');\n  const location=briefPointValue(b,'Venue / Location');\n  const clean=v=>v && !/^not specified/i.test(v) ? v : '';\n  return [clean(client)||'Client TBC', clean(eventType)||'Event', clean(location)||'Location TBC'].join(' - ');\n}\n"""
        if anchor not in s: raise SystemExit(f'{path}: masterBriefType anchor missing')
        s=s.replace(anchor,helper+anchor,1)

    old='<td><strong>${escapeHtml(b.title)}</strong></td>'
    new='<td><strong>${escapeHtml(masterDisplayTitle(b))}</strong></td>'
    if old in s:
        s=s.replace(old,new,1)

    path.write_text(s)
    print('patched',path)

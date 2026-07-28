# Bold.dk til Home Assistant

En uofficiel integration, der opretter liga- og klubsensorer ud fra de offentlige
sider på [Bold.dk](https://bold.dk). Projektet er ikke tilknyttet Bold.dk.

## Sensorer

Integrationen opretter en ligaentitet med den aktuelle stilling. For hver valgt
klub oprettes fire sensorer:

- **Placering** i ligaen
- **Seneste kamp** med modstander og resultat
- **Næste kamp** med modstander og tidspunkt, når Bold.dk viser det
- **Topscorer** med antal mål som attribut

Alle sensorer indeholder `source_url`, så data altid kan føres tilbage til siden.
Navigationselementer som "Seneste resultater" og andre ligaer bliver ikke længere
fejlagtigt udstillet som historier.

## Installation og opsætning

1. Installér repositoryet som en brugerdefineret integration via HACS, eller kopiér
   `custom_components/bold_dk` til din Home Assistant-konfiguration.
2. Genstart Home Assistant.
3. Vælg **Indstillinger → Enheder og tjenester → Tilføj integration → Bold.dk**.
4. Angiv et liganavn og URL'en til ligaens stillingsside, eksempelvis
   `https://bold.dk/fodbold/stillinger/superligaen`.
5. Integrationen finder klubberne på siden. Afkryds de klubber, du vil følge.

Der oprettes derefter en enhed for ligaen og en enhed med fire sensorer for hver
valgt klub. Data opdateres hvert 15. minut for at begrænse belastningen på Bold.dk.

Bold.dk kan ændre HTML-strukturen uden varsel. Hvis en værdi ikke findes på den
offentlige klubside, vises sensoren som ukendt frem for at gætte på værdien.

Brugerfladens danske tekster ligger direkte i integrationens `strings.json`. Der
medfølger ikke en separat dansk oversættelsesfil, så Home Assistant kan ikke blive
blokeret af en forældet eller beskadiget `translations/da.json`. Ved opgradering
fra en tidligere version skal den gamle fil slettes, før Home Assistant genstartes.

Version 0.1.1 bruger Home Assistants stabile `multi_select`-komponent i
konfigurationsflowet. Dermed kan flowet også indlæses på Home Assistant-versioner,
som ikke indeholder den nyere `SelectSelectorMode`-klasse.

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
En uofficiel Home Assistant-integration, som gør de seneste historier for dine
favoritklubber og -ligaer på [Bold.dk](https://bold.dk) til sensorer.

> Projektet er ikke udviklet, godkendt eller supporteret af Bold.dk.

## Funktioner

- Konfigureres direkte fra Home Assistants brugerflade.
- Følg enhver klub- eller ligaside på `https://bold.dk`.
- Én sensor pr. favorit med den nyeste overskrift som tilstand.
- Sensorattributter indeholder linket til den nyeste historie og op til ti historier.
- Opdaterer hvert 15. minut og bruger Home Assistants fælles HTTP-session.

## Installation

1. Kopiér `custom_components/bold_dk` til samme placering i din Home Assistant-konfiguration.
2. Genstart Home Assistant.
3. Gå til **Indstillinger → Enheder og tjenester → Tilføj integration** og søg efter **Bold.dk**.
4. Find de ønskede klub- eller ligasider på Bold.dk, og indsæt én pr. linje:

   ```text
   Brøndby IF | https://bold.dk/fodbold/klubber/broendby-if
   Superligaen | https://bold.dk/fodbold/ligaer/superligaen
   ```

Bold.dk kan ændre både adresser og HTML uden varsel. Brug derfor den URL, som
aktuelt vises i browseren, frem for at kopiere eksempeladresserne ukritisk.

## Lovlig og hensynsfuld brug

Integrationen viser links og korte metadata; den kopierer ikke artikler. Respektér
Bold.dk's vilkår. Opdateringsintervallet er bevidst sat til 15 minutter for at
begrænse belastningen.


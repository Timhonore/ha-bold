# Bold.dk til Home Assistant

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


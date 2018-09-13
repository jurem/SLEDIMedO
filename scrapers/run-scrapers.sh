#!/bin/bash

# zagon scraperjev
source main_scrapers_run_petric.sh
source main_scrapers_run_zakelj.sh

source ~/scraperTests/venv_scrapers/bin/activate

python Scraper-bistra.py
python Scraper-cerknica.py
python Scraper-danube_region.py
python scraper_delo_ljubljana.py
python scraper-digitrans.py
python scraper_dnevnik_ljubljana.py
python scraper-edulab.py
python scraper-eguts.py
python scraper-excellence_in_resti.py
python scraper-foresda.py
python Scraper-geopark-idrija.py
python scraper_gis.py
python Scraper-innorenew.py
python scraper_izvrs.py
python scraper-made_in_Danube.py
python Scraper-Mariborinfo.py
python Scraper-mkgp_gov.py
python scraper_mladina.py
python scraper_moja_obcina_ljubljana.py
python Scraper-mzi_gov.py
python Scraper-Notrajinski_park.py
python Scraper-pomurec.py
python Scraper-pomurske_novice.py
python Scraper-p_tech.py
python Scraper-PtujInfo.py
python Scraper-pzs.py
python Scraper-raz.um.py
python SCRAPER-RTV-Ljubljana.py
python scraper-senses.py
python scraper_slovenske_novice.py
python Scraper-tednik.py
python scraper_uirs.py
python Scraper-vestnik.py
python Scraper-visit-idrija.py
python SCRAPER-zgs.py
python scrapper-ecoinn.py

deactivate

# premik baze na mesto kjer bere spletna stran
yes | cp /scraperTests/SLEDIMedO/scrapers/database/articles.db ~/public_html/sql/articles.db



#!/usr/bin/env python3
"""Build the public-source channel lead research dataset.

The input names below are transcribed from the cited public directory/list pages.
No private contact data is collected. Unknown fields are deliberately null.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus, urlparse


OUT = Path(__file__).with_name("research_channels.json")
VERIFIED_ON = "2026-07-13"


SOURCES = [
    {"id": "S01", "title": "FoodBevg Kathmandu Wine, Beer & Spirits Stores - page 1", "url": "https://www.foodbevg.com/NP/Kathmandu/168940/genre/199833073363963/Wine%2C-Beer-%26-Spirits-Store", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Kathmandu liquor-store discovery; directory listing is not proof of current operation."},
    {"id": "S02", "title": "FoodBevg Kathmandu Wine, Beer & Spirits Stores - page 2", "url": "https://www.foodbevg.com/NP/Kathmandu/168940/genre/199833073363963/Wine%2C%2BBeer%2B%26%2BSpirits%2BStore/2", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Kathmandu liquor-store discovery."},
    {"id": "S03", "title": "FoodBevg Kathmandu Wine, Beer & Spirits Stores - page 3", "url": "https://www.foodbevg.com/NP/Kathmandu/168940/genre/199833073363963/Wine%2C%2BBeer%2B%26%2BSpirits%2BStore/3", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Kathmandu liquor-store discovery."},
    {"id": "S04", "title": "FoodBevg Kathmandu Wine, Beer & Spirits Stores - page 4", "url": "https://www.foodbevg.com/NP/Kathmandu/168940/genre/199833073363963/Wine%2C%2BBeer%2B%26%2BSpirits%2BStore/4", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Kathmandu liquor-store discovery."},
    {"id": "S05", "title": "FoodBevg Kathmandu Wine, Beer & Spirits Stores - page 5", "url": "https://www.foodbevg.com/NP/Kathmandu/168940/genre/199833073363963/Wine%2C%2BBeer%2B%26%2BSpirits%2BStore/5", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Kathmandu liquor-store discovery."},
    {"id": "S06", "title": "NepalYP Wine and Beer in Kathmandu", "url": "https://www.nepalyp.com/category/Wine_and_Beer/city%3AKathmandu", "source_type": "business directory", "grade": "C", "published_or_updated": "2026-07", "accessed": VERIFIED_ON, "use": "Cross-check selected liquor retailers."},
    {"id": "S07", "title": "Cybo wine, beer and liquor stores in Kathmandu", "url": "https://www.cybo.com/NP/kathmandu/wine%2C-beer-and-liquor-stores/", "source_type": "business directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Cross-check selected liquor retailers and public business phones."},
    {"id": "S08", "title": "Tripadvisor restaurants in Kathmandu", "url": "https://www.tripadvisor.com/Restaurants-g293890-Kathmandu_Kathmandu_Valley_Bagmati_Zone_Central_Region.html", "source_type": "travel platform", "grade": "C", "published_or_updated": "2026-07", "accessed": VERIFIED_ON, "use": "Current restaurant lead discovery and review-volume signal."},
    {"id": "S09", "title": "Tripadvisor restaurants in Pokhara", "url": "https://www.tripadvisor.com/Restaurants-g293891-Pokhara_Gandaki_Zone_Western_Region.html", "source_type": "travel platform", "grade": "C", "published_or_updated": "2026-07", "accessed": VERIFIED_ON, "use": "Current restaurant lead discovery."},
    {"id": "S10", "title": "Pokhara Valley hotel and restaurant market-survey annex", "url": "https://libird.org/wp-content/uploads/2022/04/LCPV-DI_Market-Survey-Report.pdf", "source_type": "research report", "grade": "B", "published_or_updated": "2022-04", "accessed": VERIFIED_ON, "use": "Second source for Pokhara hotels and restaurants; older source."},
    {"id": "S11", "title": "Tripadvisor restaurants in Sauraha", "url": "https://www.tripadvisor.com/Restaurants-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region.html", "source_type": "travel platform", "grade": "C", "published_or_updated": "2026-06", "accessed": VERIFIED_ON, "use": "Sauraha restaurant lead discovery."},
    {"id": "S12", "title": "Tripadvisor hotels in Sauraha", "url": "https://www.tripadvisor.com/Hotels-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region-Hotels.html", "source_type": "travel platform", "grade": "C", "published_or_updated": "2026-06", "accessed": VERIFIED_ON, "use": "Sauraha hotel/resort lead discovery."},
    {"id": "S13", "title": "Chitwan Chamber member database", "url": "https://ccichitwan.org.np/images/Website-images/All-Member-till-2079-1-14-2022-04-27_04_49_06.pdf", "source_type": "chamber member list", "grade": "B", "published_or_updated": "2022-04-27", "accessed": VERIFIED_ON, "use": "Bharatpur/Chitwan local business discovery; current status needs re-check."},
    {"id": "S14", "title": "Nepal Rastra Bank FX licensed entities as of 14 January 2026", "url": "https://www.nrb.org.np/fxm/licensed-entities-by-nrb-for-fx-transactions-as-on-poush-end-2082-january14-2026/", "source_type": "government regulator list", "grade": "A", "published_or_updated": "2026-01-14", "accessed": VERIFIED_ON, "use": "High-value hotel/tourism entity verification, especially Pokhara."},
    {"id": "S15", "title": "National Population and Housing Census 2021 - population composition", "url": "https://censusnepal.cbs.gov.np/results/files/result-folder/Final_Population_compostion_12_2.pdf", "source_type": "government statistics", "grade": "A", "published_or_updated": "2024", "accessed": VERIFIED_ON, "use": "City population evidence."},
    {"id": "S16", "title": "Nepal Tourism Statistics 2025", "url": "https://tourism.gov.np/content/711/nepal-tourism-statistics-2025/", "source_type": "government statistics", "grade": "A", "published_or_updated": "2026", "accessed": VERIFIED_ON, "use": "Tourism and accommodation supply context."},
    {"id": "S17", "title": "Hotel Association Pokhara", "url": "https://www.hotelspokhara.org/presidents-message/", "source_type": "industry association", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Evidence of 400+ active member hotels and association contact route."},
    {"id": "S18", "title": "Hotel Association Nepal", "url": "https://www.hotelassociationnepal.org.np/", "source_type": "industry association", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "National hotel-member access route; association says 300+ represented hotels."},
    {"id": "S19", "title": "Restaurant & Bar Association Nepal", "url": "https://rebannepal.com/", "source_type": "industry association", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Restaurant-member access route; Kathmandu/Pokhara/Sauraha/Bharatpur chapters."},
    {"id": "S20", "title": "Cheers Online Store Nepal", "url": "https://www.cheers.com.np/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Platform operating status, assortment and competitor pricing."},
    {"id": "S21", "title": "Daraz Nepal spirits category", "url": "https://www.daraz.com.np/spirits/", "source_type": "e-commerce marketplace", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Marketplace status, 342 alcohol items and visible seller/price evidence."},
    {"id": "S22", "title": "Barmandoo official site", "url": "https://barmandoo.com.np/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Late-night alcohol delivery operating status."},
    {"id": "S23", "title": "Barmandoo Google Play listing", "url": "https://play.google.com/store/apps/details?id=np.com.barmandoo", "source_type": "app store", "grade": "B", "published_or_updated": "2026-04-05", "accessed": VERIFIED_ON, "use": "Second-source operating-status and public support contact verification."},
    {"id": "S24", "title": "Drinks Nepal official site", "url": "https://drinksnepal.com/", "source_type": "company website", "grade": "B", "published_or_updated": "2026", "accessed": VERIFIED_ON, "use": "Online and physical retail status, Kathmandu address, phone, age gate."},
    {"id": "S25", "title": "Liquor Stop Kathmandu", "url": "https://www.liquorstop.com.np/liquor-shop-kathmandu-nepal", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Store address, public phone/email and imported-spirit assortment."},
    {"id": "S26", "title": "Barmandoo terms and conditions", "url": "https://barmandoo.com.np/terms-and-conditions", "source_type": "company policy", "grade": "B", "published_or_updated": "2020-10-20", "accessed": VERIFIED_ON, "use": "Declared alcohol-delivery age/ID restrictions; legal review still required."},
    {"id": "S27", "title": "Hotel Pokhara Grande official site", "url": "https://www.pokharagrande.com/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Hotel scale, dining/bar, halls and wedding facilities."},
    {"id": "S28", "title": "Hotel Barahi Pokhara official site", "url": "https://barahi.com/properties/hotel-barahi/about/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Hotel, restaurant and premium-segment verification."},
    {"id": "S29", "title": "Green Park Chitwan official site", "url": "https://www.greenparkchitwan.com/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Resort bar/restaurant and premium-segment verification."},
    {"id": "S30", "title": "Barahi Jungle Lodge official site", "url": "https://barahi.com/properties/barahi-jungle-lodge/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Luxury Chitwan lodge verification."},
    {"id": "S31", "title": "The Soaltee Kathmandu official Marriott page", "url": "https://www.marriott.com/en-us/hotels/ktmsk-the-soaltee-kathmandu-autograph-collection/overview/", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Five-star hotel, dining, bar and event-space verification."},
    {"id": "S32", "title": "NepalYP Greenline and Vesper listings", "url": "https://www.nepalyp.com/category/Wine_and_Beer/city%3AKathmandu", "source_type": "business directory", "grade": "C", "published_or_updated": "2026-07", "accessed": VERIFIED_ON, "use": "Second-source selected retail leads."},
    {"id": "S33", "title": "Brother's Liquor Shop about page", "url": "https://brothersliquor.com.np/about.php", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Premium imported spirits and Sankhamul location."},
    {"id": "S34", "title": "Darumandu about page", "url": "https://darumandu.com/about-us", "source_type": "company website", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "24/7 alcohol delivery coverage claim for Kathmandu, Lalitpur and Bhaktapur."},
    {"id": "S35", "title": "Himalayan Distillery annual report FY 2081/82", "url": "https://himalayandistillery.com/wp-content/uploads/2026/05/Annual-Report-FY-2081-82.pdf", "source_type": "company annual report", "grade": "B", "published_or_updated": "2026-05", "accessed": VERIFIED_ON, "use": "Competitor/category trend evidence; lighter and mixable drinks noted as preference trend."},
    {"id": "S36", "title": "Kathmandu hotel association", "url": "https://hotelassociationktm.org.np/", "source_type": "industry association", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Area-unit route for hotel prospecting in Kathmandu."},
    {"id": "S37", "title": "Darumandu Nepal LinkedIn company page", "url": "https://www.linkedin.com/company/darumandunepal", "source_type": "public company social page", "grade": "C", "published_or_updated": "2026", "accessed": VERIFIED_ON, "use": "Second-source company identity, service area and public business phone."},
    {"id": "S38", "title": "The Vesper House business profile", "url": "https://wanderlog.com/place/details/3333732/the-vesper-house", "source_type": "place/review directory", "grade": "C", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Second-source address, website, phone and wine-store/importer classification."},
    {"id": "S39", "title": "Brother's Liquor Shop terms", "url": "https://brothersliquor.com.np/terms.php", "source_type": "company policy", "grade": "B", "published_or_updated": None, "accessed": VERIFIED_ON, "use": "Second public page confirming ecommerce alcohol purchase terms and Sankhamul contact."},
    {"id": "S40", "title": "Liquor Stop Nepal storefront", "url": "https://liquorstop.com.np/", "source_type": "company website", "grade": "B", "published_or_updated": "2026", "accessed": VERIFIED_ON, "use": "Second public page confirming current products, imported collection and contact."},
    {"id": "S41", "title": "Daraz - Cheers Online Liquor Store", "url": "https://www.daraz.com.np/shop/cheers-online-liquor-store/", "source_type": "e-commerce marketplace storefront", "grade": "B", "published_or_updated": "2026-07", "accessed": VERIFIED_ON, "use": "Independent marketplace storefront confirming Cheers as a seller on Daraz; current operating status still needs contact verification."},
]

SOURCE_BY_ID = {s["id"]: s for s in SOURCES}


KTM_LIQUOR = """
Online Liquors-Kathmandu|Old Baneshwor Road
Beer Hub|Dhumbarahi
RARA BLUES|Handigau Marga
Koirala Mart Pvt. Ltd.|Samakhusi
Satkar Liquors|Kathmandu
Liquor Shop Kimdol|Swoyambhu, Kimdol
Moonlight Liquor Store|Kathmandu
New Muktinath Liquors|Basundhara
Online Liquor Nepal|Thamel
Liquor Shop Nepal|Asan
Roadhouse Liquors & Bitters|Kirtipur
Ailaa Suppliers|Old Baneshwor
Wishco|Baluwatar
SK Madira|Putalisadak
J C Liquors Shop|Lazimpat Road, Panipokhari
SG Trade|Mid Baneshwor
24 Hours Online Liquor Ranibari|Ranibari
New Namuna Store|Kathmandu
Mandali Liquor Store|Kathmandu
First Choice Liquor Store|New Naikap
The Next Generation Hub|Kageshwori Manohara
AA Trade Concern-Liquor Shop|Kathmandu
SNG Liquor Store|Suncity, Pepsicola
Nepal Liquor House|Samakhusi
Booze Up Liquor|Chikamugal
Appeal Liquor|Kumud Devkota Marga
Uniqor Wine & Spirits|Gaurighat
Madira Adda|Nayabuspark
24 Hours Online Liquors Store & Delivery Service|Lazimpat
Miransh Liquor World|Kalikasthan
Aaila|Kathmandu
Booze Bazaar|Shantinagar
Diamond Liquor Suppliers Pvt. Ltd.|Raniban, Balaju
Xpress Liquor Store|Kapan Shivmandir
Chiso Tatto|Bhimsengola Marg
Boozestation|Kathmandu
Anjali Wine Gallery|Basantapur
S&B Wine Shop|Lazimpat
Juju Liquor Mart|Chandol
Cheers Online Liquor Store|Kamaladi
Greenline Center Pvt. Ltd.|Durbarmarg
Royal Musk Nepal|Lazimpat
Marsi Beer|Hadigaun
Online Liquor Delivery Chabahil|Ganesh Marg, Chabahil
FM Liquor Pvt. Ltd.|Lazimpat
Raksi Nepal|Kathmandu
The Liquor Shop|Thulo Bharyang
24 Hours Online Liquor Fast Delivery|Lazimpat
Yasmalee Liquor|Boudha
Uptown Liquors Store|Chapali, Budhanilkantha
Himalayan Liquor Store|Mahankal
Nepal Craft Beer Distributors|Manbhawan
JMT Liquor Shop|Kathmandu
Blue Spirits|Soltemode, Kalimati
DH Liquor Mart|Gairidhara
MadiraLaya Kathmandu|Koteshwar
Bhojpure Beverage|Jorpati
Shubani Liquors Suppliers|Gagalphedi
M.G. Liquors|Samakhusi
Buddha Mini Grocery & Liquor Shop|Sakuna Marg
Night Liquor Shop|Kathmandu
Ghar Bar|Old Baneshwor
Aila Chen Online Liquor House|Basundhara
High Spirit Network|Kathmandu
Royal Sen Enterprises|Dhapasi, Tokha
Fantastic Liquor Shop|Swoyambhu Marg
Melody Liquor|Nayabasti
Bhairab Liquor Store|Kathmandu
Liquor Town Store|Nayabazar
Bishal Liquor Shop|Khusibu
Liquor Library|Kadaghari
Om Valley Liquors|Naxal, Naagpokhari
Raksi Point|New Baneshwor
Pasalrun Liquor|Panipokhari
RaksiWala|Ghattekulo
Alisha Cold Store|Bhakti Thapa Road
Jemisha Wine Shop|Baluwakhani
Aeeyla Premium Liquor Store|Kathmandu
Tipsy Nepal|Tripureshwor
Gokyo Liquors|Tinkune
Bottom's Up Online Liquor Store|Samakhusi
The Liquor Land|Gusingal Marg, Lalitpur
D Star Liquor Shop|New Baneshwor
Tiwari Cold Stores|Banasthali
DaruDeal Online Liquors|Koteshwor
Dibyeta Traders Pvt. Ltd.|Kapan Marg
Chambade Liquor Shop|Gokarneshwor
Drinks & Delight House|Subidhanagar, Tinkune
Booze|Thamel
Aila D Liquor|Dallu
Raksi Guff|Lazimpat
Km Madira Pasal|Manakamana Marga
The Liquor Corner|Kapan, Milan Chowk
BoozeGhar|Boudha
Aila Durbar|Lagan Tole
Kkapurdhara Liquor Shop|Kapurdhara, Samakhusi
1Shot Liquor|Maitidevi, Ghattekulo
Karki Liquor Shop|Kisipidi
R.S. Liquor Hub Nepaltar|Tarkeshwor
New BD Liquor Store|Dhungedhara
De Aila Point|Nayabazar
Daru Chaiyo|Thamel
DrinkSathi|Baneshwor
Ya Ya Madira Store|Saraswotinagar
KK's Liquor|Mehpi
Hangover Liquor Store|Guheshwori, Sanopul
NightCap Liquors Online|Kathmandu
N.S. Wine Shop|Kathmandu
ABC Liquors Shop Arubari|Jorpati
Rausi Enterprises|Madhya Marg
Liquor World Wholesale|Tokha
Golden Jar|Gyaneshwor
Fresh Liquorland|Uttardhoka
A. K. Liquors World Pvt. Ltd.|Pepsicola
A to Z Liquor Shop|Link Marg
MidNight Liquor|Nakhipot, Lalitpur
Swagatam Madira Stores|Dakshinkali
Rainbow Liquor Shop|Maitrinagar
A.T Liquor and Iceland Station|Halchowk
Pandey Liquor House|Mulpani
Uncle Jim's Liquor Store|Baluwatar
Aditi Aayan Liquor Shop|Tokha
Bhai Baa Liquor Shop|Jhatapole, Lalitpur
The Liquor Hub Jorpati|Jorpati
Online Liquor Kalanki|Kalanki
Samar Liquor Shop|Nagarjun
Solu Liquor Gallery|Kathmandu
The Vesper House|Jhamsikhel, Lalitpur
Liquor Stop Nepal|Gongabu / BG Mall area
Drinks Nepal|Maharajgunj
Brother's Liquor Shop|Sankhamul
Barmandoo|Kathmandu Valley
Darumandu|Kathmandu Valley
"""


KTM_RESTAURANTS = """
Bagaichā
Yala Cafe
Lavie Garden
Jimbu Thakali by Capital Grill - Tangal
Jimbu Thakali by Capital Grill - New Baneshwor
Nepalaya Rooftop Restaurant
Jimbu Thakali by Capital Grill - Kalimati
House of Beers
Jasper Restaurant
The Chimney Restaurant
French Creperie Kathmandu
Bao Xuan - Flavours of China
Patio - The Soaltee Kathmandu
Kakori
Edamame
Mustang Thakali by State III
The Black Gold Halal Restaurant
Hokkaido House
Toran Restaurant
Kathmandu Grill Restaurant and Wine Bar
Spize
The Best Kathmandu Kitchen
Garden Terrace Restaurant
Walnut Bistro
Nectar by Carpe Diem
Kaiser Cafe
Soko Korean Grill & Bar
Izakaya Hokkaido
SUPPER Club Dim Sum & Disco House
Carpe Diem Lounge & Bakery
Utpala Cafe
4Stories
Apricus Cafe
Odc Cafe & Restaurant
Czech Pub Nepal
House of Thakali
Nourish by Avata
H2O Cafe N Pub
Gauchan Thakali Restaurant and Bar
Chiya Pasal Restaurant
Regal Flavors Restro and Bar
Kathmandu Steak House Restaurant
Thamel Momo Hut
Gaia Restaurant
Yangling Tibetan Restaurant
Frens Kitchen Restaurant
Blueberry Kitchen & Coffee Shop
Cafe Lava
New Everest Momo Center
O' Cha
Monster Meal
Jojo's Pub
Chow Bella
Daejanggeum Korean Restaurant
Sum Cafe
Thamel Kitchen
Kirtipur Newa Lahana
Bhojan Griha
Le Sherpa
Krishnarpan Restaurant
"""


KTM_HOTELS_VENUES = """
The Soaltee Kathmandu, Autograph Collection|Tahachal|hotel
Kathmandu Marriott Hotel|Kamal Pokhari|hotel
Aloft Kathmandu Thamel|Thamel|hotel
Hyatt Regency Kathmandu|Boudha|hotel
Hyatt Place Kathmandu|Tahachal|hotel
Hyatt Centric Soalteemode Kathmandu|Soalteemode|hotel
Hilton Kathmandu|Naxal|hotel
The Dwarika's Hotel|Battisputali|hotel
Hotel Yak & Yeti|Durbar Marg|hotel
Radisson Hotel Kathmandu|Lazimpat|hotel
Vivanta Kathmandu|Jhamsikhel|hotel
Hotel Shanker|Lazimpat|hotel
Hotel Barahi Kathmandu|Kantipath|hotel
Ramada by Wyndham Kathmandu Dhumbarahi|Dhumbarahi|hotel
Dusit Princess Kathmandu|Lazimpat|hotel
Crowne Imperial|Ravi Bhavan|hotel
Fairfield by Marriott Kathmandu|Thamel|hotel
Holiday Inn Express Kathmandu Naxal|Naxal|hotel
Mercure Kathmandu Sukedhara Heights|Sukedhara|hotel
Hotel Himalaya|Kupondole|hotel
Hotel Annapurna|Durbar Marg|hotel
Gokarna Forest Resort|Gokarna|hotel
Park Village Resort|Budhanilkantha|hotel
Kathmandu Guest House|Thamel|hotel
Maya Manor Boutique Hotel|Hattisar|hotel
The Malla Hotel|Lekhnath Marg|hotel
Hotel Mulberry|Thamel|hotel
Aranya Boutique Hotel|Hattisar|hotel
Hotel Sabrina Kathmandu|Budhanilkantha|hotel
Royal Singi Hotel|Kamaladi|hotel
Amrapali Banquet|Kathmandu|banquet
Royal Empire Boutique Hotel & Banquet|Baluwatar|banquet
Heritage Garden|Sanepa|banquet
Alice Receptions|Gairidhara|banquet
Anupam Foodland & Banquet|Battisputali|banquet
"""


POKHARA_RESTAURANTS = """
Utopia Garden & Snacks Bar
Fresh Elements Restaurant
Cheli Thakali - Pokhara
Soul Origin Cafe and Restaurant
Byanjan Restaurant
Little Windows Veg & Vegan Pokhara Restaurant
360 Sky Lounge
Frituur No.1
Nonion Italian & Mediterranean Cuisine
Relax Kitchen & Bar
Fireside's Pizzeria Cafe & Bar
The Muglan Pokhara
Bulldog Restaurant and Bar
Tcity Cafe
Chinese Garden Restaurant & Bar
Fuel Bar & Grill
Med5 Restaurant
Roadhouse Cafe Pokhara
French Creperie Pokhara
Mo2's Delights Pokhara
Rosemary Kitchen Pokhara
Wendy Juice Shop
Chilly Bar & Restaurant
Asian Tea House
Rest Point Cafe & Bar
The Old Lan Hua Chinese Restaurant
Krazy Gecko
The Juicery Cafe
Moondance Restaurant & Bar
Caffe Concerto
OR2K Pokhara
Busy Bee Cafe
Paradiso Sports Bar & Grill
The Harbor Restaurant
Godfather's Pizzeria
Everest Steak House Pokhara
Pokhara Thakali Kitchen
Sarang Korean Restaurant
Rice Garden Restaurant & Bar
Sky Lounge Pokhara
"""


POKHARA_HOTELS = """
Hotel Pokhara Grande|Pardi Bazaar
Hotel Barahi Pokhara|Lakeside
Temple Tree Resort & Spa|Lakeside
Fishtail Lodge|Lakeside
Atithi Resort & Spa|Shanti Patan, Lakeside
Waterfront Resort by KGH Group|Sedi, Lakeside
Himalayan Front Hotel|Sarangkot area
Hotel Middle Path & Spa|Lakeside
Bar Peepal Resort|Pokhara-18
Dahlia Boutique Hotel|Lakeside
Dorje's Resort & Spa|Sedi Bagar
Hotel Adam|Samikopatan
Hotel Mount Kailash Resort|Lakeside
Hotel Mount View Pokhara|Lakeside
Hotel Sarowar|Lakeside
Lake View Resort|Lakeside
Hotel Landmark Pokhara|Lakeside
Hotel White Pearl|Barahi Path, Lakeside
Temple Himalaya Hotel & Spa|Street 13, Lakeside
Majestic Lake Front Hotel & Suites|Lakeside
Rupakot Resort|Rupakot
The Pavilions Himalayas|Pumdi Bhumdi
Tiger Mountain Pokhara Lodge|Kandani Danda
Begnas Lake Resort & Villas|Begnas
Hotel Iceland|Lakeside
Hotel Splendid View & Spa|Lakeside
Hotel Lake Shore|Lakeside
Hotel Karuna|Lakeside
Hotel Pokhara Batika|Gaurighat, Lakeside
Hotel Shaara|Lakeside
"""


CHITWAN_RESTAURANTS = """
KC's Restaurant and Home Pvt. Ltd.
Art Cafe Sauraha
Friends Cafe Sauraha
Kinaar Restaurant & Bar
Taxi's Restaurant
Greasy Spoon Restaurant
Royal Kitchen & Bar Sauraha
Jomsom Thakali Bhanchha Ghar
Accoustica Shisha
Himalaya Gurkha Coffee House
Cafe de Safari
Jalapeno Restaurant
Sunset View Restaurant & Bar
Bay Leaf Restaurant
Pizzeria Rosa
New Nepali Kitchen Restaurant
Chhimeki Food Hut
CGL Garden Restaurant
Fusion Restaurant & Bar Sauraha
Sichuan Hotpot Sauraha
River Park Retreat
1997 Drinks & Bites Cafe Restro
Cowboy Pub & Live Music Bar
Dutch Hippies Drink and Bites
The Hook Restaurant & Shisha Bar
Jalapeno Restaurant and Bar
Vitamin Cafe Chitwan
Mustang Thakali Restaurant & Bar Sauraha
Park View Restaurant Sauraha
The Green Park Restaurant & Bar
The Green Park Sekuwa Corner
The Narayani Kitchen
The Tandoor Palace
Third Eye Restaurant with Shisha Bar
Lucky Momo Restaurant
Narayani Bhojanalaya
Chitwan Burger House & Crunchy Fried Chicken
Shreenagar Hotel & Restaurant
Thapa Restaurant & Bar
The Jankos Family Restaurant
Lime and Lemon Lounge
Falcha Cafe Bharatpur
Cup O' Joe Bharatpur
Hungry Tom Bharatpur
Bridge Cafe Pulchowk
"""


CHITWAN_HOTELS = """
Green Park Chitwan|Sauraha
Barahi Jungle Lodge|Meghauli
Meghauli Serai, A Taj Safari|Meghauli
Kasara Chitwan|Patihani
Jungle Villa Resort|Patihani
Landmark Forest Park|Sauraha
Sapana Village Lodge|Sauraha
Hotel Jungle Crown|Sauraha
Park Safari Resort|Sauraha
Chitwan Paradise Hotel|Sauraha
Chitwan Village Resort|Sauraha
Chitwan Riverside Resort|Sauraha
Hotel Rainforest|Sauraha
Chautari Garden Resort|Sauraha
Hotel Nature Heritage|Sauraha
Tiger Residency Resort|Sauraha
Jungle Nepal Resort|Sauraha
Chitwan Forest Resort|Sauraha
Maruni Sanctuary Lodge by KGH Group|Sauraha
Motherland Resort|Sauraha
Sauraha Jungle World Resort|Sauraha
Royal Tiger Luxury Resort|Sauraha
Green Mansions Jungle Resort|Sauraha
Eden Jungle Resort|Sauraha
Hotel Rhino Land|Sauraha
Banbas Chitwan Resort|Kumroj
Hotel Royal Century|Bharatpur
The Rainbow Hotel|Bharatpur
Safari Narayani Hotel|Bharatpur / Ghatgai
Hotel Monalisa Chitwan|Sauraha
"""


ORGANIZATIONS = [
    ("Hotel Association Nepal", "Kathmandu", "industry_association", "S18"),
    ("Hotel Association Pokhara Nepal", "Pokhara", "industry_association", "S17"),
    ("Hotel Association Nepal Chitwan", "Chitwan", "industry_association", "S18"),
    ("Restaurant & Bar Association Nepal", "Kathmandu", "industry_association", "S19"),
    ("REBAN Pokhara", "Pokhara", "industry_association", "S19"),
    ("REBAN Sauraha", "Chitwan", "industry_association", "S19"),
    ("REBAN Bharatpur", "Bharatpur", "industry_association", "S19"),
    ("Chitwan Chamber of Commerce and Industry", "Bharatpur", "chamber", "S13"),
    ("District Hotel Business Association Kathmandu", "Kathmandu", "industry_association", "S36"),
    ("Daraz Nepal", "Kathmandu", "ecommerce", "S21"),
]


OFFICIAL_OVERRIDES = {
    "Liquor Stop Nepal": {"website": "https://www.liquorstop.com.np/liquor-shop-kathmandu-nepal", "phone": "+977 9803451035", "email": "liquorstopnepal@gmail.com", "source_ids": ["S25", "S40"]},
    "Drinks Nepal": {"website": "https://drinksnepal.com/", "phone": "+977 9764595290", "source_ids": ["S24"]},
    "Brother's Liquor Shop": {"website": "https://brothersliquor.com.np/about.php", "phone": "+977 9803822865", "email": "dpkmgr88@gmail.com", "source_ids": ["S33", "S39"]},
    "Barmandoo": {"website": "https://barmandoo.com.np/", "phone": "+977 9802088800", "email": "support@barmandoo.com.np", "source_ids": ["S22", "S23"]},
    "Darumandu": {"website": "https://darumandu.com/about-us", "phone": "+977 9768728150", "email": "darumandunepal@gmail.com", "source_ids": ["S34", "S37"]},
    "Cheers Online Liquor Store": {"website": "https://www.cheers.com.np/", "source_ids": ["S20", "S41"]},
    "Cheers Online Store Nepal": {"website": "https://www.cheers.com.np/", "source_ids": ["S20", "S41"]},
    "Daraz Nepal": {"website": "https://www.daraz.com.np/spirits/", "source_ids": ["S21"]},
    "Hotel Pokhara Grande": {"website": "https://www.pokharagrande.com/", "source_ids": ["S27", "S14", "S09"]},
    "Hotel Barahi Pokhara": {"website": "https://barahi.com/properties/hotel-barahi/about/", "source_ids": ["S28", "S09"]},
    "Fishtail Lodge": {"source_ids": ["S14", "S09", "S10"]},
    "Atithi Resort & Spa": {"source_ids": ["S14", "S10"]},
    "Byanjan Restaurant": {"source_ids": ["S09", "S10"]},
    "Fresh Elements Restaurant": {"source_ids": ["S09", "S10"]},
    "Med5 Restaurant": {"source_ids": ["S09", "S10"]},
    "Rosemary Kitchen Pokhara": {"source_ids": ["S09", "S10"]},
    "Green Park Chitwan": {"website": "https://www.greenparkchitwan.com/", "source_ids": ["S29", "S12"]},
    "Barahi Jungle Lodge": {"website": "https://barahi.com/properties/barahi-jungle-lodge/", "source_ids": ["S30", "S12"]},
    "The Green Park Restaurant & Bar": {"source_ids": ["S13", "S11"]},
    "The Soaltee Kathmandu, Autograph Collection": {"website": "https://www.marriott.com/en-us/hotels/ktmsk-the-soaltee-kathmandu-autograph-collection/overview/", "source_ids": ["S31", "S08"]},
    "Patio - The Soaltee Kathmandu": {"website": "https://www.marriott.com/en-us/hotels/ktmsk-the-soaltee-kathmandu-autograph-collection/dining/", "source_ids": ["S31", "S08"]},
    "Kakori": {"website": "https://www.marriott.com/en-us/hotels/ktmsk-the-soaltee-kathmandu-autograph-collection/dining/", "source_ids": ["S31", "S08"]},
    "Garden Terrace Restaurant": {"website": "https://www.marriott.com/en-us/hotels/ktmsk-the-soaltee-kathmandu-autograph-collection/dining/", "source_ids": ["S31", "S08"]},
    "The Vesper House": {"website": "https://www.vesperhouse.com/", "phone": "+977 1-5409240", "source_ids": ["S06", "S38"]},
    "Greenline Center Pvt. Ltd.": {"source_ids": ["S01", "S06"]},
}


def rows(block: str):
    for raw in block.strip().splitlines():
        parts = [p.strip() for p in raw.split("|")]
        yield parts


def map_url(name: str, city: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{name}, {city}, Nepal")


def source_urls(source_ids):
    return [SOURCE_BY_ID[s]["url"] for s in source_ids if s in SOURCE_BY_ID]


def source_origins(source_ids):
    origins = set()
    for url in source_urls(source_ids):
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            origins.add(host)
    return origins


leads = []
seen = set()


def add_lead(name, city, category, area=None, source_ids=None, address=None):
    city = {
        "Kathmandu": "Kathmandu Valley",
        "Chitwan": "Chitwan/Bharatpur",
        "Bharatpur": "Chitwan/Bharatpur",
    }.get(city, city)
    key = (re.sub(r"\W+", "", name.casefold()), city.casefold())
    if key in seen:
        return
    seen.add(key)
    source_ids = list(source_ids or [])
    override = OFFICIAL_OVERRIDES.get(name, {})
    if override.get("source_ids"):
        source_ids = override["source_ids"]
    high_priority = len(source_origins(source_ids)) >= 2 and bool(override)
    if category in {"liquor_retail", "ecommerce", "instant_delivery"}:
        score = 76 if high_priority else 61
        entry = "以小批量试销、礼盒/宴请场景和进口烈酒差异化切入；先核验是否有合法酒类销售资格与白酒类目空间。"
        contact = "website/contact form, public business phone, then Messenger/WhatsApp only if the business publishes it"
    elif category in {"hotel", "resort", "banquet"}:
        score = 74 if high_priority else 58
        entry = "从F&B负责人、宴会销售或采购切入，提议合规闭门品鉴、宴会套餐或礼赠试销；不先谈长期独家。"
        contact = "LinkedIn search for F&B Manager/Procurement, official hotel contact, then phone appointment"
    elif category == "restaurant_bar":
        score = 70 if high_priority else 55
        entry = "从负责人/F&B经理切入，先做小杯慢饮与菜品搭配的封闭品鉴，再评估按杯/按瓶试销。"
        contact = "Google Maps/official page verification, then Facebook Messenger or public business phone"
    else:
        score = 68 if high_priority else 52
        entry = "请求会员名录、采购活动或合规商务对接机会；协会仅作名单入口，不视为成交渠道。"
        contact = "official email/phone and event inquiry"
    grade = "A" if score >= 65 else "B" if score >= 50 else "C"
    evidence = "KNOWN" if high_priority else "NEEDS_VERIFY"
    current_status = "可首次接触" if evidence == "KNOWN" and high_priority else "待验证"
    map_link = map_url(name, city)
    urls = source_urls(source_ids)
    # Google Maps is a verification route, not counted as a positive confirmation.
    record = {
        "lead_id": None,
        "enterprise_name": name,
        "english_name": name,
        "local_name": None,
        "city": city,
        "area": area,
        "full_address": address or area,
        "google_maps_url": map_link,
        "customer_type": category,
        "main_business": category.replace("_", " "),
        "imported_spirits_status": "INFERRED" if category in {"liquor_retail", "ecommerce", "instant_delivery", "hotel", "resort", "restaurant_bar"} else "NEEDS_VERIFY",
        "upper_midmarket_status": "INFERRED" if high_priority or category in {"hotel", "resort"} else "NEEDS_VERIFY",
        "website": override.get("website"),
        "facebook": None,
        "instagram": None,
        "linkedin": None,
        "tiktok": None,
        "public_phone": override.get("phone"),
        "public_email": override.get("email"),
        "whatsapp_or_viber": None,
        "decision_maker_name": None,
        "decision_maker_title": None,
        "decision_maker_public_contact": None,
        "source_ids": source_ids,
        "evidence_urls": urls,
        "source_updated": [SOURCE_BY_ID[s]["published_or_updated"] for s in source_ids if s in SOURCE_BY_ID],
        "last_verified_date": VERIFIED_ON if high_priority else None,
        "source_accessed_date": VERIFIED_ON,
        "evidence_status": evidence,
        "evidence_note": "KNOWN means a current official page or two public list sources were found; it does not prove willingness to buy. NEEDS_VERIFY means only a directory/list discovery source was found and current operation must be checked.",
        "recommended_contact_method": contact,
        "recommended_language": "English first; Nepali version requires native-speaker review",
        "recommended_product_entry": entry,
        "lead_score": {"score": score, "grade": grade, "basis_status": "INFERRED", "reason": "Public-source fit signal only; execution ability, credit, import-liquor experience and trial willingness remain unverified."},
        "priority": "high" if high_priority else "standard",
        "cross_source_status": "KNOWN: two or more independent public domains" if high_priority else "NEEDS_VERIFY: fewer than two independent public domains",
        "current_status": current_status,
        "next_action": "Open the Maps query and official/social page; confirm operating status, alcohol license/assortment and responsible buyer before outreach.",
        "risk_note": "No non-public personal data. Do not treat a directory phone or an unverified social number as a decision-maker contact. Respect local alcohol-promotion rules and platform terms."
    }
    leads.append(record)


for i, (name, area) in enumerate(rows(KTM_LIQUOR)):
    add_lead(name, "Kathmandu Valley", "liquor_retail", area, [f"S{1 + min(i // 30, 4):02d}"])

for (name,) in rows(KTM_RESTAURANTS):
    add_lead(name, "Kathmandu Valley", "restaurant_bar", None, ["S08"])

for name, area, typ in rows(KTM_HOTELS_VENUES):
    add_lead(name, "Kathmandu Valley", typ, area, ["S18", "S08"] if name in OFFICIAL_OVERRIDES else ["S18"])

for (name,) in rows(POKHARA_RESTAURANTS):
    add_lead(name, "Pokhara", "restaurant_bar", "Lakeside / Pokhara", ["S09"])

for name, area in rows(POKHARA_HOTELS):
    add_lead(name, "Pokhara", "hotel", area, ["S14"])

for (name,) in rows(CHITWAN_RESTAURANTS):
    add_lead(name, "Chitwan/Bharatpur", "restaurant_bar", "Sauraha / Bharatpur", ["S11"])

for name, area in rows(CHITWAN_HOTELS):
    add_lead(name, "Chitwan/Bharatpur", "resort", area, ["S12"])

for name, city, typ, sid in ORGANIZATIONS:
    add_lead(name, city, typ, None, [sid])

for idx, lead in enumerate(leads, 1):
    lead["lead_id"] = f"NP-FJ-{idx:04d}"


platform_methods = [
    {"platform": "Google Maps", "status": "KNOWN", "use": "Find and verify hotels, restaurants, bars and liquor stores; inspect category, address, hours, recent reviews and official website button.", "search_examples": ["liquor store Kathmandu", "wine shop Lalitpur", "Chinese restaurant Thamel", "5 star hotel Pokhara", "resort Sauraha", "banquet Bharatpur"], "workflow": ["Run city+category search", "capture exact place URL", "exclude permanently closed/duplicate branch", "check recent review/activity", "open official site/social", "record public business contact only"], "dedupe_key": "normalized name + phone/domain + map coordinates", "verification_rule": "Recent activity plus a second official/social source for high priority", "automation_boundary": "AI may prepare search/dedupe; manual browser review is needed for Maps results and terms compliance."},
    {"platform": "Facebook / Messenger", "status": "KNOWN", "use": "Check recent business activity and contact pages that publish Messenger.", "search_examples": ["site:facebook.com liquor Kathmandu", "Pokhara restaurant Lakeside Facebook", "Sauraha resort Facebook"], "workflow": ["Open official-looking page", "check address/domain match", "check posts within recent months", "record page URL", "send one concise business message only after compliance gate"], "dedupe_key": "page URL + matching address/domain", "verification_rule": "Page must match business identity and show current activity; never treat personal mobile/profile as company decision maker without explicit public business context.", "automation_boundary": "No automated messaging, login bypass, mass scraping or repeated unsolicited follow-up."},
    {"platform": "LinkedIn", "status": "KNOWN", "use": "Find F&B Manager, Procurement Manager, General Manager, Beverage Manager, Banquet Sales, Owner/Director and Corporate Administration roles.", "search_examples": ["(F&B OR Food Beverage) Manager Kathmandu hotel", "procurement manager Pokhara resort", "owner liquor distributor Nepal", "corporate admin procurement Nepal"], "workflow": ["Verify employer", "record public professional profile URL only", "prioritize role relevance", "send connection note", "move to official email/phone after reply"], "dedupe_key": "company + person + current role", "verification_rule": "Employment must be current and public; do not infer personal phone/email.", "automation_boundary": "No automated connection requests or extraction that violates LinkedIn terms."},
    {"platform": "Tripadvisor / Booking / Agoda", "status": "KNOWN", "use": "Lead discovery, segment signal and active-property check; not a decision-maker database.", "search_examples": ["Kathmandu fine dining", "Pokhara hotels", "Sauraha resorts"], "workflow": ["Capture property name", "check current review volume/date", "follow official-site link", "find official business contact", "score banquet/bar/restaurant fit"], "dedupe_key": "property name + address/domain", "verification_rule": "Cross-check with official site or association/regulator list before high-priority outreach.", "automation_boundary": "Respect platform terms; no login/anti-bot bypass."},
    {"platform": "Associations and chambers", "status": "KNOWN", "use": "Request member directories, events and chapter introductions; not direct proof of purchase intent.", "search_examples": ["HAN members", "HAPN members", "REBAN Pokhara", "REBAN Sauraha", "Chitwan Chamber members"], "workflow": ["Use official association contact", "ask for public member directory or event calendar", "offer compliance-reviewed trade tasting", "individually verify each resulting company"], "dedupe_key": "legal/member business name + address", "verification_rule": "Membership list age must be recorded; old lists remain NEEDS_VERIFY.", "automation_boundary": "No claim that association endorsement exists until written confirmation."},
    {"platform": "Telephone / WhatsApp / Viber", "status": "KNOWN", "use": "Confirm responsible buyer and book meetings after business identity is verified.", "search_examples": [], "workflow": ["Call public business number", "ask who handles wine/spirits/F&B procurement", "request permission to send a one-page introduction", "log consent and next step"], "dedupe_key": "E.164 phone + business", "verification_rule": "Personal number only if explicitly published for business use.", "automation_boundary": "AI may draft scripts/reminders; no autonomous calls, impersonation or bulk WhatsApp/Viber messaging."},
]


city_scoring = [
    {"city": "Kathmandu Valley", "raw_evidence": [{"metric": "Kathmandu Metropolitan population 2021", "value": 862400, "unit": "people", "status": "KNOWN", "source_id": "S15"}, {"metric": "Kathmandu population density 2021", "value": 17440, "unit": "people/km2", "status": "KNOWN", "source_id": "S15"}, {"metric": "restaurant result count visible on Tripadvisor", "value": 1440, "unit": "listings", "status": "KNOWN", "source_id": "S08"}, {"metric": "liquor-store discovery leads in this dataset", "value": sum(1 for x in leads if x["city"] == "Kathmandu Valley" and x["customer_type"] == "liquor_retail"), "unit": "directory leads", "status": "COMPUTED", "source_ids": ["S01", "S02", "S03", "S04", "S05", "S06", "S07"]}], "score_components": {"consumption_capacity": 14, "hospitality_density": 15, "imported_spirits_base": 14, "business_tourism_banquets": 10, "distributor_retail_resources": 10, "china_asia_dining": 9, "digital_reach": 10, "competitive_gap": 5, "execution_delivery": 5}, "total": 92, "confidence": "medium-high", "status": "INFERRED", "priority": 1, "entry_condition": "国代确认SKU、供价、库存、合法传播边界与可配送区域后，先做20-30家高优先级试点。", "caution": "竞争最强、获客噪音最高；不得把人口/门店密度直接等同于汾酒接受度。"},
    {"city": "Pokhara", "raw_evidence": [{"metric": "Pokhara Metropolitan population 2021", "value": 513504, "unit": "people", "status": "KNOWN", "source_id": "S15"}, {"metric": "Hotel Association Pokhara active members", "value": 400, "unit": "members (association says over 400)", "status": "KNOWN", "source_id": "S17"}, {"metric": "Tripadvisor restaurant result count", "value": 476, "unit": "listings", "status": "KNOWN", "source_id": "S09"}, {"metric": "NRB current licensed hotel/tourism entities", "value": None, "unit": "entities", "status": "NEEDS_VERIFY", "source_id": "S14"}], "score_components": {"consumption_capacity": 11, "hospitality_density": 14, "imported_spirits_base": 11, "business_tourism_banquets": 9, "distributor_retail_resources": 7, "china_asia_dining": 7, "digital_reach": 8, "competitive_gap": 7, "execution_delivery": 3}, "total": 77, "confidence": "medium", "status": "INFERRED", "priority": 2, "entry_condition": "Kathmandu试销模型跑通，且国代能承诺Pokhara补货时效；以Lakeside酒店/餐厅集中开发。", "caution": "旅游季节性明显，人口与游客场景不能重复计算。"},
    {"city": "Chitwan/Bharatpur", "raw_evidence": [{"metric": "Bharatpur Metropolitan population 2021", "value": 369268, "unit": "people", "status": "KNOWN", "source_id": "S15"}, {"metric": "Sauraha restaurant result count", "value": 48, "unit": "listings", "status": "KNOWN", "source_id": "S11"}, {"metric": "Chitwan Chamber member database", "value": None, "unit": "hospitality members in old list", "status": "NEEDS_VERIFY", "source_id": "S13"}], "score_components": {"consumption_capacity": 8, "hospitality_density": 9, "imported_spirits_base": 7, "business_tourism_banquets": 8, "distributor_retail_resources": 6, "china_asia_dining": 4, "digital_reach": 6, "competitive_gap": 8, "execution_delivery": 3}, "total": 59, "confidence": "medium-low", "status": "INFERRED", "priority": 3, "entry_condition": "先锁定Sauraha高端度假酒店与Bharatpur宴会/商务场景，并确认配送经济性。", "caution": "Sauraha旅游带与Bharatpur城市消费是两种场景，名单应分区管理。"},
]


platform_status = [
    {"platform": "Cheers Online Store Nepal", "operating_status": "KNOWN: website accessible and current products visible", "sells_alcohol": "KNOWN", "coverage": "NEEDS_VERIFY", "imported_spirits": "KNOWN", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "NEEDS_VERIFY", "age_verification": "NEEDS_VERIFY", "contact": None, "priority": "high", "source_ids": ["S20", "S21"], "next_step": "Use official contact to request brand/vendor onboarding pack, commission, age gate and coverage in writing."},
    {"platform": "Daraz Nepal", "operating_status": "KNOWN: spirits category visible", "sells_alcohol": "KNOWN: 342 category items visible at access time", "coverage": "Listings show Bagmati and Gandaki sellers; exact deliverability must be postcode-tested", "imported_spirits": "KNOWN", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "Marketplace logistics; alcohol-specific process NEEDS_VERIFY", "age_verification": "NEEDS_VERIFY", "contact": "Daraz seller center/help", "priority": "high", "source_ids": ["S21"], "next_step": "Ask category manager for written alcohol seller requirements; do not infer general seller rules apply unchanged."},
    {"platform": "Barmandoo", "operating_status": "KNOWN: official site accessible; app updated 2026-04-05", "sells_alcohol": "KNOWN", "coverage": "Kathmandu stated in app description; exact zones NEEDS_VERIFY", "imported_spirits": "KNOWN", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "Claims 45-minute / late-night delivery", "age_verification": "KNOWN: terms require adult recipient and photo ID, but local legal review required", "contact": "+9779802088800; support@barmandoo.com.np", "priority": "high", "source_ids": ["S22", "S23", "S26"], "next_step": "Request partner onboarding, commission, service area, inventory model and current age-verification SOP."},
    {"platform": "Drinks Nepal", "operating_status": "KNOWN: 2026 site accessible", "sells_alcohol": "KNOWN", "coverage": "Kathmandu Valley / all-Nepal claim; exact SKU zones NEEDS_VERIFY", "imported_spirits": "KNOWN", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "Online delivery plus physical Maharajgunj store", "age_verification": "KNOWN: site uses 21+ age gate; legal sufficiency NEEDS_VERIFY", "contact": "+977-9764595290", "priority": "high", "source_ids": ["S24"], "next_step": "Approach as retailer/brand partner; request commercial and compliance terms."},
    {"platform": "Liquor Stop Nepal", "operating_status": "KNOWN: official page accessible", "sells_alcohol": "KNOWN", "coverage": "Kathmandu / nationwide delivery claim; NEEDS_VERIFY", "imported_spirits": "KNOWN", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "Fast-delivery claim", "age_verification": "NEEDS_VERIFY", "contact": "+977 9803451035; liquorstopnepal@gmail.com", "priority": "high", "source_ids": ["S25"], "next_step": "Pitch limited SKU trial and request sell-through reporting."},
    {"platform": "Darumandu", "operating_status": "KNOWN: official about page accessible", "sells_alcohol": "KNOWN", "coverage": "Kathmandu, Lalitpur, Bhaktapur claim", "imported_spirits": "INFERRED", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "24/7 claim", "age_verification": "NEEDS_VERIFY", "contact": None, "priority": "medium", "source_ids": ["S34"], "next_step": "Verify current app/order flow, service zones and compliance process before commercial discussion."},
    {"platform": "Foodmandu", "operating_status": "KNOWN: general delivery platform exists; alcohol category not confirmed in this research", "sells_alcohol": "NEEDS_VERIFY", "coverage": "NEEDS_VERIFY", "imported_spirits": "NEEDS_VERIFY", "onboarding_entity": "NEEDS_VERIFY", "licenses": "NEEDS_VERIFY", "fees_commission": None, "delivery": "NEEDS_VERIFY", "age_verification": "NEEDS_VERIFY", "contact": None, "priority": "low until confirmed", "source_ids": [], "next_step": "Ask Foodmandu in writing whether sealed spirits are an accepted category; do not assume."},
]


competitors = [
    {"brand_or_segment": "Johnnie Walker", "type": "imported Scotch whisky", "status": "KNOWN", "evidence": "Multiple SKUs visible on Cheers/Daraz; Black Label 750ml was shown at NPR 7,700 on Daraz at access time.", "source_ids": ["S20", "S21"], "implication": "Strong reference brand; Fenjiu will be price-compared against familiar whisky even though category and taste differ."},
    {"brand_or_segment": "Chivas Regal", "type": "imported Scotch whisky", "status": "KNOWN", "evidence": "Brand filter/products visible on Cheers and Drinks Nepal.", "source_ids": ["S20", "S24"], "implication": "Competes in gifting/business-dinner cues and has far higher category familiarity."},
    {"brand_or_segment": "Jack Daniel's", "type": "imported American whiskey", "status": "KNOWN", "evidence": "Multiple sizes visible on Daraz and Cheers.", "source_ids": ["S20", "S21"], "implication": "Recognizable imported alternative with mixability advantage for first-time spirit drinkers."},
    {"brand_or_segment": "Old Durbar", "type": "Nepal-produced premium whisky", "status": "KNOWN", "evidence": "12-year and 15-year variants visible on Cheers; 12-year 750ml shown at NPR 5,000.", "source_ids": ["S20"], "implication": "Local premium story plus lower education burden; direct shelf and gifting competitor."},
    {"brand_or_segment": "Khukri Rum", "type": "Nepal rum", "status": "KNOWN", "evidence": "Khukri Coronation and other variants visible on Cheers/Daraz.", "source_ids": ["S20", "S21"], "implication": "Strong Nepal identity and gifting recognition; Fenjiu should not rely only on national-origin storytelling."},
    {"brand_or_segment": "Local traditional spirits (Aila/Raksi)", "type": "traditional distilled alcohol", "status": "KNOWN at category level; formal-channel brands vary", "evidence": "Many retailer names and local menus reference Aila/Raksi; exact consumption and price need fieldwork.", "source_ids": ["S01", "S11"], "implication": "Creates a conceptual bridge to grain spirits, but does not prove willingness to buy Chinese baijiu."},
    {"brand_or_segment": "Fenjiu / Chinese baijiu on Nepal e-commerce", "type": "Chinese baijiu", "status": "NEEDS_VERIFY", "evidence": "Targeted searches did not surface a current Nepal Fenjiu/Moutai/Wuliangye product listing on major checked platforms. Absence from search is not proof of no market presence.", "source_ids": ["S20", "S21", "S24", "S25"], "implication": "Potential white space but also indicates category-education and discoverability risk; verify offline Chinese-community channels."},
]


counts_by_city = Counter(x["city"] for x in leads)
counts_by_type = Counter(x["customer_type"] for x in leads)
priority_counts = Counter(x["priority"] for x in leads)


payload = {
    "metadata": {
        "project": "Fenjiu Nepal B2B/B2C channel research",
        "generated_on": VERIFIED_ON,
        "cutoff_date": VERIFIED_ON,
        "lead_count": len(leads),
        "target": 300,
        "target_met": len(leads) >= 300,
        "counts_by_city": dict(counts_by_city),
        "counts_by_type": dict(counts_by_type),
        "priority_counts": dict(priority_counts),
        "truth_labels": ["KNOWN", "INFERRED", "COMPUTED", "NEEDS_VERIFY", "BLOCKED"],
        "important_limitations": [
            "A directory listing proves only that a public listing was found, not that the business is currently open or willing/authorized to buy imported spirits.",
            "Most decision-maker names, emails and messaging numbers are null because they were not safely verified as public business contacts.",
            "High-priority means good public-source fit, at least two cited URLs, and at least two independent source hostnames; it is not human verification, a credit decision, or sales acceptance.",
            "Google Maps URLs are search routes for human verification, not evidence that the exact result has already been manually confirmed.",
            "All alcohol outreach, sampling and content must pass Nepal legal/platform compliance review and age-gating requirements."
        ]
    },
    "city_scoring": city_scoring,
    "platform_acquisition_methods": platform_methods,
    "ecommerce_and_delivery_status": platform_status,
    "competitor_snapshot": competitors,
    "leads": leads,
    "sources": SOURCES,
}


OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload["metadata"], ensure_ascii=False, indent=2))

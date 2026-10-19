"""Domain lexicon features for the Tour Ceylon incident classifier.

Each incident type has a group of regular expressions (synonyms, stems and
common phrases). The transformer counts matches per group, giving the Random
Forest a small set of strong, dense signals that generalise to wording that
never appeared in the training messages.

This module must stay importable as ``app.ml.incident_features`` because the
saved model (joblib) references these classes by import path.
"""

from __future__ import annotations

import re

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin

LEXICON: dict[str, list[str]] = {
    "fire": [r"\bfire\b", r"\bflames?\b", r"\bsmoke\b", r"\bsmoky\b", r"\bburn(?:ing|t|s|ed)?\b", r"\bblaze\b",
             r"\bablaze\b", r"\bignit", r"\bsparks?\b", r"\bfire ?(?:brigade|fighters?|alarm|exit)\b", r"\bon fire\b"],
    "accident": [r"\b(?:smashed|slammed|ran|crashed|drove|ploughed|plowed|went) into\b", r"\bhit (?:a|the|an) (?:cyclist|pedestrian|man|woman|child|kid|boy|girl|dog|cow|pole|wall|tree)\b", r"\bstruck by\b|\btipped over\b|\bover the edge\b|\boff the road\b|\brolled down\b", r"\baccident\b", r"\bcrash", r"\bcollid", r"\bcollision\b", r"\brun over\b", r"\bknocked (?:me )?down\b",
                 r"\bover ?turn", r"\brolled over\b", r"\bflipped\b", r"\bskid", r"\bpile ?up\b", r"\bswerv", r"\bairbags?\b",
                 r"\brear[- ]ended\b", r"\bhead[- ]on\b", r"\bfell off (?:the |my |a )?(?:bike|scooter|motor ?bike|motorcycle|tuk ?tuk)",
                 r"\b(?:car|bus|van|lorry|truck|tuk ?tuks?|taxi|cab|scooter|motor ?bikes?|motorcycle|jeep|three[- ]wheeler|vehicle|tractor|minibus)\b",
                 r"\b(?:road|highway|expressway|junction|roundabout)\b"],
    "medical": [r"\bfit\b|\bfits\b|\bmigraine\b|\bdiarrh|\bweak\b|\bshaking\b.{0,10}\bfloor\b", r"\bchest\b", r"\bbreath", r"\bfaint", r"\bcollaps(?:ed|ing)\b", r"\bunconscious\b", r"\bunresponsive\b",
                r"\bseizure|\bconvuls|\bhaving a fit\b", r"\bfever\b|\btemperature\b", r"\bvomit|\bthrowing up\b", r"\ballerg",
                r"\basthma|\binhaler\b", r"\bdiabet|\binsulin\b|\bblood sugar\b", r"\bstroke\b", r"\bheart\b", r"\bpain\b|\bpainful\b",
                r"\bbleed", r"\bchok(?:e|ed|ing)\b", r"\blabou?r\b|\bpregnan|\bwater broke\b", r"\bpills\b|\boverdose|\bmedicine\b",
                r"\bdizzy\b|\bdizziness\b", r"\bbroken (?:leg|arm|hip|ankle|wrist|bone|collarbone|rib)|\bbroke my\b",
                r"\bambulance\b", r"\bdoctor\b", r"\bhospital\b", r"\bsick\b", r"\bpassed out\b|\bpassing out\b", r"\bnumb\b",
                r"\blips are blue\b|\bgasping\b"],
    "sexual": [r"\brap(?:e|ed|ing|ist)\b", r"\bsexual", r"\bgrop", r"\bmolest", r"\btouch(?:ed|ing)? (?:me|my|her)\b",
               r"\bbreasts?\b", r"\bprivate parts?\b", r"\bbetween my legs\b", r"\bundress", r"\bspiked\b|\bdrugged\b",
               r"\bforced (?:me|himself|herself)\b|\bforced (?:to|into) (?:have )?sex", r"\bconsent\b", r"\brubb(?:ed|ing) (?:himself|against)",
               r"\bexposed himself\b", r"\binappropriately\b", r"\bsex\b"],
    "theft": [r"\bswip(?:e|ed)\b|\bnick(?:ed)?\b|\bpinch(?:ed)?\b|\byank|\blifted my\b|\bran off with\b|\btook off with\b|\bheld us up\b|\bhold[- ]?up\b", r"\bburgl", r"\bstol(?:e|en)\b", r"\bsteal", r"\bthie(?:f|ves)\b", r"\brob(?:bed|bery|ber|bers|bing)?\b", r"\bmugg",
              r"\bpickpocket", r"\bsnatch", r"\bburglar", r"\bransack", r"\bbroke into\b|\bbroken into\b",
              r"\b(?:took|grabbed|ripped|taken|gone|vanished|disappeared)\b.{0,25}\b(?:phone|wallet|bag|laptop|camera|purse|watch|money|cash|backpack|rucksack|iphone|jewel)",
              r"\b(?:phone|wallet|bag|laptop|camera|purse|watch|money|cash|backpack|rucksack|iphone|jewel\w*)\b.{0,25}\b(?:taken|gone|vanished|missing|disappeared)\b",
              r"\b(?:gun|knife)\s?point\b"],
    "assault": [r"\bslamm?ed (?:my|his|her) head\b|\bscratch(?:ed)? (?:me|my)\b|\bhit (?:me|my|him|her|us) with\b|\bthrew .{0,15} at (?:me|us)\b", r"\bpunch", r"\bkick", r"\bslap", r"\bbeat(?:en|ing)?\b", r"\bstab", r"\bhit (?:me|my|him|her)\b",
                r"\bheadbutt", r"\bassault", r"\bfight\b|\bfighting\b", r"\bsmash", r"\bknife\b|\bmachete\b|\bweapon\b|\bstick\b|\bbrick\b|\bbottle\b",
                r"\bchok(?:e|ed) me\b|\bstrangl", r"\bjumped me\b", r"\bbruis", r"\battack(?:ed|ing)? (?:me|my|us)\b", r"\bdragged\b"],
    "disaster": [r"\bearth (?:moved|shook|is shaking)\b|\bbuilding shook\b|\briver (?:rose|is rising)\b|\bswept the bridge\b|\bcame down the (?:mountain|hill)\b|\bmud\b", r"\bflood", r"\blandslide|\bmud ?slide|\bmud and rocks\b", r"\btsunami\b", r"\bcyclone\b", r"\bstorm\b",
                 r"\bearthquake|\btremor|\bground is shaking\b|\bshaking\b", r"\bmonsoon\b", r"\bheavy rain\b|\braining\b",
                 r"\bunder ?water\b", r"\bevacuat", r"\bdam\b", r"\bburst its banks\b|\boverflow", r"\bhillside\b|\bhill\b",
                 r"\broof (?:blew|off|tore)\b|\bwinds?\b", r"\bsirens?\b", r"\bwater (?:is )?rising\b|\bsea is rising\b"],
    "missing": [r"\bcan(?:\'|no)?t reach\b|\bnobody knows where\b|\bno one (?:has seen|knows where)\b|\blost track of\b|\bunaccounted\b|\bwhere (?:she|he) is\b", r"\bmissing\b", r"\bcan(?:'|no)?t find\b|\bcannot find\b", r"\bcan(?:'|no)?t locate\b",
                r"\blost (?:my|our) (?:son|daughter|child|kid|friend|wife|husband|mother|mum|mom|father|dad|sister|brother|grand\w+|uncle|aunt|partner|boyfriend|girlfriend)\b",
                r"\bdisappear", r"\bvanish", r"\b(?:hasn'?t|has not|didn'?t|did not|never) (?:come back|came back|returned|return|arrived|got back|come home|came home)\b",
                r"\bnot been seen\b|\blast seen\b", r"\bwander", r"\bran away\b", r"\bphone is (?:off|switched off)\b|\bnot answering\b",
                r"\bmemory problems\b|\bdementia\b|\balzheimer"],
    "lost": [r"\blost my way\b|\b(?:group|we) (?:is|are|\'re) lost\b|\blost (?:near|on|in) (?:the )?(?:peak|forest|mountain|trail|jungle|park|hills?|woods)\b", r"\blost (?:on|in) the\b|\bwe(?:'re| are) lost\b|\bi(?:'m| am) lost\b|\bgot lost\b", r"\btrail\b|\bhik(?:e|ing)\b|\btrek",
             r"\bstranded\b", r"\bstuck\b", r"\btrapped (?:in|on) (?:a|the) (?:ravine|gully|cave|cliff|rock|slope)", r"\bcliff\b|\bravine\b|\bgully\b|\bslope\b|\bledge\b",
             r"\brescue\b", r"\bgps\b|\bcoordinates\b|\bno signal\b|\bbattery\b|\bphone is at\b", r"\bjungle\b|\bforest\b|\bmountain\b|\bpeak\b",
             r"\bway (?:back|out)\b|\bfind (?:our|my) way\b|\bwrong (?:path|trail)\b|\bpath\b", r"\bfog\b|\bmist\b|\bdark\b|\bsunset\b"],
    "harassment": [r"\bfollow", r"\bstalk", r"\bharass", r"\bthreat", r"\bintimidat", r"\bstar(?:e|ing)\b", r"\bwatching me\b",
                   r"\bcatcall", r"\byell|\bshout", r"\bblackmail", r"\btext(?:s|ing)? me\b|\bmessages\b|\bcalling\b", r"\boutside my (?:door|room)\b",
                   r"\bunsafe\b", r"\bphotograph|\bphotos of me\b", r"\bkeeps\b|\bwon'?t (?:stop|leave)\b", r"\brude\b|\bgestures\b"],
    "animal": [r"\bsnakes?\b|\bcobra\b|\bviper\b|\bpython\b", r"\bdogs?\b", r"\bmonkeys?\b", r"\belephants?\b", r"\bboar\b",
               r"\bcrocodiles?\b", r"\bbees?\b|\bwasps?\b|\bhornets?\b|\bswarm\b", r"\bjellyfish\b", r"\bscorpion\b|\bspider\b|\bcentipede\b",
               r"\bleopard\b|\bbear\b|\bbuffalo\b|\bbull\b|\bcow\b|\bhorse\b", r"\bbit(?:e|ten|es)?\b", r"\bstung\b|\bstings?\b",
               r"\bantivenom\b|\brabies\b|\bvenom", r"\banimal\b|\bwildlife\b|\bwild\b", r"\bcharged\b|\bchased\b",
               r"\bsea urchin\b|\bstingray\b|\bleech"],
    "drowning": [r"\bdrown", r"\bswim", r"\bcurrent\b|\brip\b|\briptide\b", r"\bwaves?\b", r"\bwent under\b|\bgoing under\b|\bunder the water\b|\bdidn'?t come up\b|\bresurface",
                 r"\bpool\b", r"\bsea\b|\bocean\b", r"\briver\b|\blake\b|\bcanal\b|\blagoon\b|\breservoir\b", r"\bwaterfall\b",
                 r"\bbeach\b|\bshore\b", r"\bcapsiz|\bsink(?:ing)?\b|\bsank\b", r"\bboat\b|\bkayak\b|\bcanoe\b|\bferry\b|\braft\b",
                 r"\boverboard\b|\bpier\b", r"\blifeguard", r"\bsurf", r"\bswept\b|\bdragged out\b|\bpulled out\b", r"\bin the water\b|\bwater\b",
                 r"\bcan'?t swim\b"],
    "passport": [r"\bpassports?\b", r"\bvisa\b", r"\bdocuments?\b|\bpapers\b", r"\bembassy\b|\bhigh commission\b|\bconsulate\b",
                 r"\bid card\b|\bidentity\b|\bboarding pass\b|\beta\b|\bdriving (?:permit|licen[cs]e)\b"],
    "fraud": [r"\bscam", r"\bfraud", r"\bfake\b", r"\bcheat|\bconned\b|\btricked\b", r"\bover ?charg|\bcharged\b",
              r"\bcard\b", r"\bbank\b|\baccount\b", r"\batm\b", r"\btransactions?\b|\bpayments?\b|\btransfer", r"\bdeposit\b|\brefund\b",
              r"\bskim|\bclon", r"\bphishing\b|\bsms\b|\bhack", r"\bwithdraw", r"\bmoney changer\b|\bcurrency\b|\bnotes\b",
              r"\bgems?\b|\bsapphires?\b|\bbooking\b|\bpaid\b|\bpay\b"],
    "other": [r"\bgas leak\b|\bsmell of gas\b|\bgas\b", r"\bexplo", r"\bbomb\b", r"\bgun ?shots?\b|\bshooting\b|\bshots\b",
              r"\briot\b|\bprotest", r"\bhostage\b|\bkidnap|\bholding (?:us|me|my)\b|\bagainst (?:our|my) will\b",
              r"\b(?:building|balcony|wall|roof|stage|crane|scaffolding)\b.{0,12}\bcollaps|\bcollaps\w* (?:building|balcony|wall)|\bbalcony\b", r"\belectric|\belectrocut|\bpower line\b",
              r"\btoxic\b|\bchemical\b|\bfumes\b", r"\bstampede\b|\bcrowd crush\b", r"\bjump\b", r"\barmed\b",
              r"\blocked (?:in|inside)\b|\bcan'?t get out\b", r"\bsuspicious\b|\bunattended\b", r"\bdanger\b",
              r"\bhelp (?:me|us)\b|\bsend help\b|\bcall me\b|\bcan'?t (?:explain|say)\b"],
}

GROUPS = list(LEXICON)
_COMPILED = {g: [re.compile(p, re.I) for p in pats] for g, pats in LEXICON.items()}


def lexicon_vector(text: str) -> np.ndarray:
    t = (text or "").lower().replace("’", "'")
    out = np.zeros(len(GROUPS) * 2, dtype=np.float32)
    for i, g in enumerate(GROUPS):
        hits = sum(1 for rx in _COMPILED[g] if rx.search(t))
        out[i] = hits
        out[len(GROUPS) + i] = 1.0 if hits else 0.0
    return out


def lexicon_hits(text: str) -> dict[str, int]:
    vec = lexicon_vector(text)
    return {g: int(vec[i]) for i, g in enumerate(GROUPS) if vec[i]}


class LexiconFeatures(BaseEstimator, TransformerMixin):
    """Counts (and presence flags) of each incident lexicon group."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return sparse.csr_matrix(np.vstack([lexicon_vector(x) for x in X]))

    def get_feature_names_out(self, input_features=None):
        return np.array([f"lex_{g}" for g in GROUPS] + [f"has_{g}" for g in GROUPS])

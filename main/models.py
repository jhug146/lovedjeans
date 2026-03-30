from django.db import models
import uuid, re, json, os


TITLE_MAX_LENGTH = 80

class SearchManager(models.Manager):
    DEFAULTS = {
        "gen": "%",
        "ws": False,
        "il": False,
        "br": False,
        "st": False,
        "col": False,
        "con": False,
        "cl": False,
        "search": "",
        "pg": "1",
        "ord": "rnd"
    }
    def search(self, parameters):
        for param in self.DEFAULTS.keys():
            if param not in parameters:
                parameters[param] = self.DEFAULTS[param]

        qs = self.filter(price__gt=0)

        if type(parameters['gen']) is list:
            valid_genders = [g for g in parameters['gen'] if g in ('men', 'women')]
            if valid_genders:
                qs = qs.filter(gender__in=valid_genders)

        search = parameters['search'][0] if type(parameters['search']) is list else parameters['search']
        for word in search.split(" "):
            if word:
                qs = qs.filter(title__icontains=word)

        for param, field in zip(
            ('ws', 'il', 'br', 'st', 'col', 'cl', 'con'),
            ('size', 'insideLeg', 'brand', 'legStyle', 'colour', 'closure', 'ebayCondition')
        ):
            if parameters[param]:
                qs = qs.filter(**{f"{field}__in": parameters[param]})

        ordering = parameters['ord'][0] if type(parameters['ord']) is list else parameters['ord']
        if ordering == 'lp':
            qs = qs.order_by('price')
        elif ordering == 'hp':
            qs = qs.order_by('-price')
        elif ordering == 'mrf':
            qs = qs.order_by('-sku')

        try:
            page = int(parameters['pg'][0])
        except (ValueError, IndexError):
            page = 1

        total = qs.count()
        items = list(qs[45*(page-1):45*page])
        return items, total


class Orders(models.Model):
    shipping = models.CharField(max_length=300, default="Not Specified")
    title = models.CharField(max_length=100)
    sku = models.CharField(max_length=10)
    sale_date = models.DateTimeField(auto_now_add=True)
    checked = models.BooleanField(default=False)
    def __str__(self):
        return self.title

class Jean(models.Model):
    title = models.CharField(max_length=100)
    sku = models.CharField(max_length=10)
    description = models.CharField(max_length=1000)
    ebayCondition = models.CharField(max_length=20)
    tagWidth = models.IntegerField()
    tagLength = models.IntegerField()
    insideLeg = models.IntegerField()
    hem = models.IntegerField()
    outsideLeg = models.IntegerField()
    rise = models.IntegerField()
    waist = models.IntegerField()
    condition1 = models.CharField(max_length=250)
    condition2 = models.CharField(max_length=250)
    condition3 = models.CharField(max_length=250)
    price = models.FloatField()
    brand = models.CharField(max_length=25)
    colour = models.CharField(max_length=10)
    insideLegMeasured = models.CharField(max_length=20)
    sizeType = models.CharField(max_length=20)
    model = models.CharField(max_length=100)
    closure = models.CharField(max_length=15)
    gender = models.CharField(max_length=10)
    exactMaterial = models.CharField(max_length=120)
    feature = models.CharField(max_length=15)
    fabricWash = models.CharField(max_length=60)
    fit = models.CharField(max_length=10)
    garmentCare = models.CharField(max_length=30)
    legStyle = models.CharField(max_length=15)
    occasion = models.CharField(max_length=15)
    size = models.IntegerField()
    tagSize = models.CharField(max_length=15)
    measuredSize = models.CharField(max_length=25)
    notes = models.CharField(max_length=35)
    waistCirc = models.CharField(max_length=6)
    riseIS = models.CharField(max_length=200)
    womenUKSize = models.CharField(max_length=15)
    inseam = models.CharField(max_length=6)
    riseInches = models.CharField(max_length=2000)
    paths = models.CharField(max_length=600)

    objects = SearchManager()
    def __str__(self):
        return self.sku
    @property
    def image_title(self):
        if self.paths:
            try:
                dir = f"/root/lovedjeans/staticfiles/media/product-images/{self.sku}/"
                image_num = len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])
            except:
                image_num = 12
            return [("/staticfiles/media/product-images/" + self.sku + "/" + self.title + "_" + str(i) + ".jpg").replace(" ","-") for i in range(image_num)]
        else:
            return ""
    @property
    def page_title(self):
        page_title = f"{self.gender} {self.model} {self.measuredSize} - Lovedjeans"
        return page_title
    class Meta:
        db_table = 'products'


class FormValues:
    selectors = {
        'ws': ('26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','42','48','50'),
        'il': ('26','28','30','32','34','36','38','40'),
        'st': ('Straight','Slim','Skinny','Relaxed','Regular','Flared','Classic','Bootcut','Tapered','Wide-Leg'),
        'br': ('7 For All Mankind','AllSaints','Diesel','EDWIN','G-Star','HUGO BOSS','Lee','Levis','Nudie','Replay','SuperDry','Tommy Hilfiger','Wrangler'),
        'col': ('Blue','Black','Grey','Red','White','Green','Yellow','Pink'),
        'con': ('Used','New With Tags'),
        'cl': ('Zip','Button'),
        'ord': ('bm', 'lp', 'hp', 'mrf')
    }
    def __init__(self, request):
        if hasattr(request, "GET"): 
            if 'm' in request.GET:
                self.mobile_open = False
        else:
            self.mobile_open = True
        self.final = {}
        req = dict(request)
        if 'gen' in req:
            genders = ((req['gen'],)) if (type(req['gen']) is str) else (req['gen'])
            print(('men' in genders, 'women' in genders))
            self.final['gender'] = ('men' in genders, 'women' in genders)
        for category,options in self.selectors.items():
            self.final[category] = []
            for i,option in enumerate(options):
                if category in tuple(request):
                    self.final[category].append((option, option in req[category]))
                else:
                    self.final[category].append((option, 0))
        if "search" in req.keys():
            self.final["search"] = req["search"][0]

#Analytics models

class Views(models.Model):
    name = models.CharField(max_length=128)
    views = models.IntegerField()
    day = models.DateField(auto_now_add=True)

class Sessions(models.Model):
    session_id = models.CharField(max_length=32)
    day = models.DateField(auto_now_add=True)

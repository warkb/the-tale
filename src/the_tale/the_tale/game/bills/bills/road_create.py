
import smart_imports

smart_imports.all()


class BaseForm(forms.BaseUserForm):
    place_1 = dext_fields.ChoiceField(label='Первый город')
    place_2 = dext_fields.ChoiceField(label='Второй город')

    path = dext_fields.CharField(label='Путь')

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        self.fields['place_1'].choices = places_storage.places.get_choices()
        self.fields['place_2'].choices = places_storage.places.get_choices()

    def clean(self):
        cleaned_data = super().clean()

        place_1 = places_storage.places.get(int(cleaned_data['place_1']))
        place_2 = places_storage.places.get(int(cleaned_data['place_2']))

        if roads_logic.road_between_places(place_1, place_2) is not None:
            raise django_forms.ValidationError('Дорога между городами уже проложена')

        if place_1.id == place_2.id:
            raise django_forms.ValidationError('Дорогу можно проложить только между разными городами')

        path_suitables = roads_logic.is_path_suitable_for_road(start_x=place_1.x,
                                                               start_y=place_1.y,
                                                               path=cleaned_data['path'])

        if not path_suitables.is_NO_ERRORS:
            raise django_forms.ValidationError(path_suitables.text)


class UserForm(BaseForm):
    pass


class ModeratorForm(BaseForm, forms.ModeratorFormMixin):
    pass


class RoadCreate(base_bill.BaseBill):
    type = relations.BILL_TYPE.ROAD_CREATE

    UserForm = UserForm
    ModeratorForm = ModeratorForm

    CAPTION = 'Строительство дороги'
    DESCRIPTION = 'Создаёт дорогу между указанными городами. Подробнее про дороги можно узнать в Путеводителе (раздел о городах).'

    def __init__(self, place_1_id=None, place_2_id=None, path=None, old_place_1_name_forms=None, old_place_2_name_forms=None):
        super().__init__()
        self.place_1_id = place_1_id
        self.place_2_id = place_2_id
        self.path = path

        self.old_place_1_name_forms = old_place_1_name_forms
        self.old_place_2_name_forms = old_place_2_name_forms

        if self.old_place_1_name_forms is None and self.place_1_id is not None:
            self.old_place_1_name_forms = self.place_1.utg_name

        if self.old_place_2_name_forms is None and self.place_2_id is not None:
            self.old_place_2_name_forms = self.place_2.utg_name

    @property
    def place_1(self):
        return places_storage.places[self.place_1_id]

    @property
    def place_2(self):
        return places_storage.places[self.place_2_id]

    @property
    def actors(self):
        return [self.place_1, self.place_2]

    def user_form_initials(self):
        return {'place_1': self.place_1_id,
                'place_2': self.place_2_id,
                'path': self.path}

    @property
    def place_1_name_changed(self):
        return self.old_place_1_name != self.place_1.name

    @property
    def place_2_name_changed(self):
        return self.old_place_2_name != self.place_2.name

    @property
    def old_place_1_name(self):
        return self.old_place_1_name_forms.normal_form()

    @property
    def old_place_2_name(self):
        return self.old_place_2_name_forms.normal_form()

    def initialize_with_form(self, user_form):
        self.place_1_id = int(user_form.c.place_1)
        self.place_2_id = int(user_form.c.place_2)
        self.path = user_form.c.path

        self.old_place_1_name_forms = self.place_1.utg_name
        self.old_place_2_name_forms = self.place_2.utg_name

    def has_meaning(self):
        if roads_logic.road_between_places(self.place_1, self.place_2) is not None:
            return False

        if self.place_1_id == self.place_2_id:
            return False

        path_suitables = roads_logic.is_path_suitable_for_road(start_x=self.place_1.x,
                                                               start_y=self.place_1.y,
                                                               path=self.path)
        return path_suitables.is_NO_ERRORS

    def apply(self, bill=None):
        if not self.has_meaning():
            return

        roads_logic.create_road(place_1=self.place_1,
                                place_2=self.place_2,
                                path=self.path)

    def serialize(self):
        return {'type': self.type.name.lower(),
                'place_1_id': self.place_1_id,
                'place_2_id': self.place_2_id,
                'old_place_1_name_forms': self.old_place_1_name_forms.serialize(),
                'old_place_2_name_forms': self.old_place_2_name_forms.serialize(),
                'path': self.path}

    @classmethod
    def deserialize(cls, data):
        obj = cls()
        obj.place_1_id = data['place_1_id']
        obj.place_2_id = data['place_2_id']
        obj.old_place_1_name_forms = utg_words.Word.deserialize(data['old_place_1_name_forms'])
        obj.old_place_2_name_forms = utg_words.Word.deserialize(data['old_place_2_name_forms'])
        obj.path = data['path']

        return obj

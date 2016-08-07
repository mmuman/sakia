from ..component.controller import ComponentController
from .model import InformationsModel
from .view import InformationsView
from sakia.tools.decorators import asyncify


class InformationsController(ComponentController):
    """
    The informations component
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the informations component

        :param sakia.gui.informations.view.InformationsView view: the view
        :param sakia.gui.informations.model.InformationsModel model: the model
        """
        super().__init__(parent, view, model)
        self.init_view_text()

    @property
    def informations_view(self):
        """
        :rtype: sakia.gui.informations.view.InformationsView
        """
        return self.view

    @classmethod
    def create(cls, parent, app, **kwargs):
        account = kwargs['account']
        community = kwargs['community']

        view = InformationsView(parent.view)
        model = InformationsModel(None, app, account, community)
        informations = cls(parent, view, model)
        model.setParent(informations)
        return informations

    @property
    def view(self) -> InformationsView:
        return self._view

    @property
    def model(self) -> InformationsModel:
        return self._model

    @asyncify
    async def init_view_text(self):
        """
        Initialization of text in informations view
        """
        referentials = self.model.referentials()
        self.view.set_rules_text_no_dividend()
        self.view.set_general_text_no_dividend()
        self.view.set_text_referentials(referentials)
        params = await self.model.parameters()
        self.view.set_money_text(params, self.model.short_currency())
        self.view.set_wot_text(params)
        self.refresh_localized_data()

    @asyncify
    async def refresh_localized_data(self):
        """
        Refresh localized data in view
        """
        localized_data = await self.model.get_localized_data()
        if localized_data:
            self.view.set_general_text(localized_data)
            self.view.set_rules_text(localized_data)
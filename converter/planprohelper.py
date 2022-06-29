import planpromodel

x_shift = 4533770.0
y_shift = 5625780.0


class PlanProHelper(object):

    def __init__(self, plan_pro_file_name):
        self.root_object = planpromodel.parse(plan_pro_file_name + ".ppxml", silence=True)

    def get_number_of_fachdaten(self):
        return len(self.root_object.LST_Planung.Fachdaten.Ausgabe_Fachdaten)

    def get_container_by_fachdaten_id(self, fachdaten_id):
        return self.root_object.LST_Planung.Fachdaten.Ausgabe_Fachdaten[fachdaten_id].LST_Zustand_Ziel.Container

    def find_geo_kanten_by_top_kante_uuid(self, container, top_kante_uuid):
        geo_kanten = container.GEO_Kante
        result = []
        for geo_kante in geo_kanten:
            if geo_kante.ID_GEO_Art.Wert == top_kante_uuid:
                result.append(geo_kante)
        return result

    def get_coordinates_of_geo_knoten(self, container, geo_knoten_uuid):
        geo_punkt = self.find_geo_punkt_by_geo_knoten_uuid(container, geo_knoten_uuid)
        x = float(geo_punkt.GEO_Punkt_Allg.GK_X.Wert) - x_shift
        y = float(geo_punkt.GEO_Punkt_Allg.GK_Y.Wert) - y_shift
        return x, y

    def find_geo_punkt_by_geo_knoten_uuid(self, container, geo_knoten_uuid):
        geo_punkte = container.GEO_Punkt
        for geo_punkt in geo_punkte:
            if geo_punkt.ID_GEO_Knoten.Wert == geo_knoten_uuid:
                return geo_punkt
        return None

    def find_signals_at_top_kante(self, top_kante_uuid):
        signals_at_top_kante = []
        for i in range(0, self.get_number_of_fachdaten()):
            container = self.get_container_by_fachdaten_id(i)
            signals = container.Signal
            for signal in signals:
                if signal.Signal_Real is None:
                    continue  # No fictitious signals
                if signal.Signal_Real.Signal_Real_Aktiv is None or (signal.Signal_Real.Signal_Real_Aktiv.Signal_Funktion.Wert != "Einfahr_Signal" and signal.Signal_Real.Signal_Real_Aktiv.Signal_Funktion.Wert != "Ausfahr_Signal" and signal.Signal_Real.Signal_Real_Aktiv.Signal_Funktion.Wert != "Block_Signal"):
                    continue  # take only Einfahr and Ausfahr signals
                references = signal.Punkt_Objekt_TOP_Kante
                for reference in references:
                    if reference.ID_TOP_Kante.Wert == top_kante_uuid:
                        signals_at_top_kante.append(signal)
        return signals_at_top_kante

    
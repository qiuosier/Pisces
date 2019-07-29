from Aries.visual.plotly import PlotlyFigure


class Resources(list):
    def plot(self):
        x = []
        y = []
        for resource in self:
            v = resource.get("valueQuantity")
            if not v:
                continue
            t = resource.get("effectiveDateTime")
            x.append(t)
            y.append(v.get("value"))
        fig = PlotlyFigure().line(x, y, name=self[0].get("code").get("text"))
        return fig


class Observation:
    pass


class Laboratory:
    def __init__(self, entries):
        self.entries = entries

    @property
    def count(self):
        return len(self.entries)

    def group_by_code(self):
        groups = dict()
        for entry in self.entries:
            resource = entry.get("resource")
            if not resource:
                continue
            codes = resource.get("code", dict()).get("coding", [])
            for code_dict in codes:
                code = code_dict.get("code")
                resources = groups.get(code, Resources())
                resources.append(resource)
                groups[code] = resources
        return groups

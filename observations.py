from Aries.visual.plotly import PlotlyFigure


class Resources(list):
    def plot(self):
        x = []
        y = []
        h = []
        l = []
        # This function processes only the first reference range.
        # Multiple reference ranges are interpreted as an "OR".
        # https://www.hl7.org/fhir/observation-definitions.html#Observation.referenceRange
        # TODO: Make sure reference range and value have the same unit.
        for resource in self:
            v = resource.get("valueQuantity")
            if not v:
                continue
            t = resource.get("effectiveDateTime")
            x.append(t)
            y.append(v.get("value"))
            r = resource.get("referenceRange")
            if r:
                r = r[0]
                high = r.get("high", {}).get("value")
                h.append(high)
                low = r.get("low", {}).get("value")
                l.append(low)
            else:
                h.append(None)
                l.append(None)

        fig = PlotlyFigure(legend=dict(x=0, y=1.25)).line(
            x, y, name=self[0].get("code").get("text")
        ).line(
            x, h, name="high", line_color='red',
        ).line(
            x, l, name="low", line_color='indigo',
        )
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

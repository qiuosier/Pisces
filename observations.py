import datetime
import html
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

        x_limit = x
        if len(x) == 1:
            x_m = datetime.datetime.strptime(x[0], "%Y-%m-%dT%H:%M:%SZ")
            x_r = datetime.datetime.strftime(x_m + datetime.timedelta(days=1), "%Y-%m-%dT%H:%M:%SZ")
            x_l = datetime.datetime.strftime(x_m - datetime.timedelta(days=1), "%Y-%m-%dT%H:%M:%SZ")
            x_limit = [x_l, x_m, x_r]
            l = l * 2
            h = h * 2


        fig = PlotlyFigure(legend=dict(x=0, y=1.25)).line(
            x, y, name=self[0].get("code").get("text") if self else ""
        ).line(
            x_limit, h, name="Reference Range - High", line_color='red',
        ).line(
            x_limit, l, name="Reference Range - Low", line_color='indigo',
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
        """Groups results by code.
        """
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
            if not codes:
                text = resource.get("code", dict()).get("text")
                if text:
                    html.escape(text)
                else:
                    text = "None"
                resources = groups.get(text, Resources())
                resources.append(resource)
                groups[text] = resources
        # Sort the resources in each group
        for key in groups.keys():
            resources = groups[key]
            resources.sort(key=lambda x:x.get("effectiveDateTime"), reverse=True)
            groups[key] = resources
        return groups

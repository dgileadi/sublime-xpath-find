import sublime
import sublime_plugin
import xml.etree.ElementTree as ET
from io import StringIO


class FileWrapper:
    def __init__(self, source):
        self.source = source
        self.lineno = -1

    def read(self, bytes):
        self.lineno += 1
        s = self.source.readline()
        return s


class XPathGenerateCommand(sublime_plugin.TextCommand):
    xml_tree = None
    line_map = None
    parent_map = None

    def run(self, edit):
        selections = self.view.sel()
        response = ""
        path = self.xpath_generate(selections[0])
        if path != None:
            response = "/".join(path)
        sublime.set_clipboard(response)
        sublime.status_message('XPath: {0}'.format(response))

    def xpath_generate(self, region):
        if not self.xml_tree:
            self.line_map = {}
            xml_raw = self.view.substr(sublime.Region(0, self.view.size()))
            xml_raw_io = FileWrapper(StringIO(xml_raw))

            try:
                context = ET.iterparse(xml_raw_io, events=("start", "end"))
                context = iter(context)
                event, self.xml_tree = next(context)

                for event, elem in context:
                    if xml_raw_io.lineno not in self.line_map:
                        self.line_map[xml_raw_io.lineno] = [elem]
                    elif elem not in self.line_map[xml_raw_io.lineno]:
                        self.line_map[xml_raw_io.lineno].append(elem)

                self.parent_map = dict((c, p) for p in self.xml_tree.getiterator() for c in p)
            except Exception as e:
                sublime.error_message(str(e))
                return

        tag = None
        if region.a > 0:
            pt_str = self.view.substr(region.a - 1)
            while region.a > 0 and pt_str != ":" and pt_str != "<" and pt_str != "/":
                region.a -= 1
                pt_str = self.view.substr(region.a - 1)
        region.b = region.a
        pt_str = self.view.substr(region.b)
        while pt_str != "/" and pt_str != ">" and pt_str != " " and pt_str != "\t" and pt_str != "\n":
            region.b += 1
            pt_str = self.view.substr(region.b)
        tag = self.view.substr(region)

        el = None
        candidates = self.line_map[self.view.rowcol(region.a)[0]]
        if candidates != None:
            for candidate in candidates:
                if candidate.tag == tag:
                    el = candidate
                    break

        if el != None:
            xpath = [el.tag]
            while el in self.parent_map and self.parent_map[el] in self.parent_map:
                el = self.parent_map[el]
                xpath.insert(0, el.tag)

            return xpath
        else:
            sublime.status_message('XPath not found')

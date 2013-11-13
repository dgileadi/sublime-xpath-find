import sublime
import sublime_plugin
import xml.etree.ElementTree as ET
from io import StringIO


class FileWrapper:
    def __init__(self, source):
        self.source = source
        self.lineno = -1

    def read(self, bytes):
        s = self.source.readline()
        self.lineno += 1
        return s


class XPathFindCommand(sublime_plugin.TextCommand):
    xml_tree = None
    query_last = ''

    def run(self, edit):
        window = self.view.window()
        window.show_input_panel('XPath',
                                self.query_last,
                                self.on_input_done,
                                self.on_input_change, self.on_input_cancel)

    def on_input_done(self, value):
        self.query_last = value
        self.xpath_find(value)

    def on_input_change(self, value):
        self.query_last = value
        self.xpath_find(value, False)

    def on_input_cancel(self):
        # When canceling, forget the parsed tree.
        self.xml_tree = None

    def xpath_find(self, expr, parse=True):
        if parse or not self.xml_tree:
            xml_raw = self.view.substr(sublime.Region(0, self.view.size()))
            xml_raw_io = FileWrapper(StringIO(xml_raw))

            try:
                context = ET.iterparse(xml_raw_io, events=("start", "end"))
                context = iter(context)
                event, self.xml_tree = next(context)

                for event, elem in context:
                    if event == "start":
                        elem.attrib["sourceline"] = xml_raw_io.lineno

            except Exception as e:
                sublime.error_message(str(e))
                return

        self.view.sel().clear()

        try:
            result = self.xml_tree.findall(expr)
        except Exception as e:
            sublime.status_message(str(e))
            return

        result_type = type(result)

        if result_type is list:
            sublime.status_message('XPath: found {0} match(es) for {1}'.format(len(result), expr))

            shown = False
            for node in result:
                # Look for the first character of the tag
                # and add it to the selection.
                # The "tag" package will highlight
                # where it starts and where it ends.
                i = 0
                while True:
                    pt = self.view.text_point(int(node.attrib["sourceline"]), i)
                    pt_str = self.view.substr(pt)
                    i += 1
                    if pt_str != ' ' and pt_str != '\t':
                        break

                pt = self.view.text_point(int(node.attrib["sourceline"]), i)
                r = sublime.Region(pt)
                self.view.sel().add(r)
                if shown == False:
                    self.view.show(pt)
                    shown = True
        else:
            sublime.status_message('XPath result: {0} for {1}'.format(result, expr))

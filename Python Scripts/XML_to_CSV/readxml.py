from lxml import etree


def get_xml_items(file_path, id_range):
    """
    Get XML items
    :param file_path: Input file location
    :param id_range: Tags unique identifiers
    :return: XML tags
    :rtype:
    """
    xml_items = []
    for event, element in etree.iterparse(file_path, tag=etree.Element):
        if event == 'end':
            for item in _get_element_items(element, id_range):
                if item:
                    xml_items.append(item)
        element.clear()
    return xml_items


def _get_element_items(element, id_range):
    """
    Get element tags and values/text
    :param element: XML element
    :param id_range: Tags unique identifiers
    :return: XML items
    :rtype: List object
    """
    xml_items = []
    split_tag = element.tag.split('_')
    for item in split_tag:
        if (len(item) == 1 and item.isalpha()) and item in id_range:
            xml_tag = "_".join([i.strip() for i in split_tag if i not in id_range])
            xml_items.append(('id', item))
            xml_items.append((xml_tag, element.text))
    yield xml_items

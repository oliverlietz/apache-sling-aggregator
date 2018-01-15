#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.request
import xml.dom.minidom
import xml.etree.ElementTree

repo_blacklist = []

maven_blacklist = ['slingstart-maven-plugin']


def read_opml():
    response = urllib.request.urlopen('https://gitbox.apache.org/repos/asf?a=opml')
    opml = response.read()
    return xml.etree.ElementTree.fromstring(opml)


def read_pom(repo):
    url = 'https://gitbox.apache.org/repos/asf?p=%s.git;a=blob_plain;f=pom.xml;hb=HEAD' % (repo)
    response = urllib.request.urlopen(url)
    if response.getcode() == 200:
        pom = response.read()
        try:
            return xml.etree.ElementTree.fromstring(pom)
        except:
            return None
    else:
        return None


def filter_sling_repos(opml):
    repos = []
    result = opml.findall(".//outline[@xmlUrl]")
    pattern = re.compile('p=(.*)\.git')
    for element in result:
        xmlUrl = element.attrib['xmlUrl']
        if xmlUrl.startswith('https://gitbox.apache.org/repos/asf?p=sling-'):
            urls = re.findall(pattern, xmlUrl)
            if len(urls) == 1:
                url = urls[0]
                if url not in repo_blacklist:
                    repos.append(url)
    repos.sort()
    return repos


def read_project(pom):
    project = {}
    project['artifactId'] = pom.findall('./{http://maven.apache.org/POM/4.0.0}artifactId')[0].text.strip()
    project['name'] = pom.findall('./{http://maven.apache.org/POM/4.0.0}name')[0].text.strip()
    try:
        project['description'] = pom.findall('./{http://maven.apache.org/POM/4.0.0}description')[0].text.strip()
    except:
        project['description'] = None
    return project


def map_projects(repos):
    mapping = {}
    for repo in repos:
        pom = read_pom(repo)
        if pom:
            mapping[repo] = read_project(pom)
        else:
            mapping[repo] = None
    return mapping


def build_repo_manifest(mapping):
    manifest = xml.etree.ElementTree.Element('manifest')
    manifest.append(build_repo_remote('origin', 'https://gitbox.apache.org/repos/asf/', 'master'))
    manifest.append(build_repo_remote('oliverlietz', 'https://github.com/oliverlietz/', 'master'))
    project = xml.etree.ElementTree.Element('project')
    project.set('path', '.')
    project.set('name', 'apache-sling-aggregator')
    project.set('remote', 'oliverlietz')
    manifest.append(project)
    for repo in sorted(mapping):
        path = repo if mapping[repo] is None else mapping[repo]['artifactId']
        project = xml.etree.ElementTree.Element('project')
        project.set('path', path)
        project.set('name', repo)
        project.set('remote', 'origin')
        manifest.append(project)

    return manifest


def build_repo_remote(name, fetch, revision):
    remote = xml.etree.ElementTree.Element('remote')
    remote.set('name', name)
    remote.set('fetch', fetch)
    remote.set('revision', revision)
    return remote


def build_maven_aggregator_pom(mapping):
    pom = xml.etree.ElementTree.Element('project')
    pom.set('xmlns', 'http://maven.apache.org/POM/4.0.0')
    pom.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    pom.set('xsi:schemaLocation', 'http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd')

    modelVersion = xml.etree.ElementTree.Element('modelVersion')
    modelVersion.text = '4.0.0'
    pom.append(modelVersion)

    parent = build_pom_parent()
    pom.append(parent)

    artifactId = xml.etree.ElementTree.Element('artifactId')
    artifactId.text = 'apache-sling-aggregator'
    pom.append(artifactId)
    version = xml.etree.ElementTree.Element('version')
    version.text = '1-SNAPSHOT'
    pom.append(version)
    packaging = xml.etree.ElementTree.Element('packaging')
    packaging.text = 'pom'
    pom.append(packaging)
    name = xml.etree.ElementTree.Element('name')
    name.text = 'Apache Sling – Aggregator'
    pom.append(name)

    modules = xml.etree.ElementTree.Element('modules')
    pom.append(modules)
    projects = sorted(filter(None, mapping.values()), key=lambda project: project['artifactId'])
    for project in projects:
        artifactId = project['artifactId']
        if artifactId and artifactId not in maven_blacklist:
            module = xml.etree.ElementTree.Element('module')
            module.text = artifactId
            modules.append(module)

    build = build_pom_build()
    pom.append(build)
    return pom


def build_pom_parent():
    parent = xml.etree.ElementTree.Element('parent')
    groupId = xml.etree.ElementTree.Element('groupId')
    groupId.text = 'org.apache.sling'
    parent.append(groupId)
    artifactId = xml.etree.ElementTree.Element('artifactId')
    artifactId.text = 'sling'
    parent.append(artifactId)
    version = xml.etree.ElementTree.Element('version')
    version.text = '32'
    parent.append(version)
    relativePath = xml.etree.ElementTree.Element('relativePath')
    parent.append(relativePath)
    return parent


def build_pom_build():
    build = xml.etree.ElementTree.Element('build')
    plugins = xml.etree.ElementTree.Element('plugins')
    build.append(plugins)
    rat = build_pom_build_plugin_skip('org.apache.rat', 'apache-rat-plugin')
    plugins.append(rat)
    ianal = build_pom_build_plugin_skip('org.codehaus.mojo', 'ianal-maven-plugin')
    plugins.append(ianal)
    return build


def build_pom_build_plugin_skip(group_id, artifact_id):
    plugin = xml.etree.ElementTree.Element('plugin')
    groupId = xml.etree.ElementTree.Element('groupId')
    groupId.text = group_id
    plugin.append(groupId)
    artifactId = xml.etree.ElementTree.Element('artifactId')
    artifactId.text = artifact_id
    plugin.append(artifactId)
    configuration = xml.etree.ElementTree.Element('configuration')
    plugin.append(configuration)
    skip = xml.etree.ElementTree.Element('skip')
    skip.text = 'true'
    configuration.append(skip)
    return plugin


def build_index_markdown(mapping):
    markdown = []
    markdown.append('# Apache Sling – Aggregator')
    markdown.append('|||||')
    markdown.append('--- | --- | --- | ---')
    for repo in sorted(mapping):
        if mapping[repo] is None:
            row = '[{repo}](https://github.com/apache/{repo})|||'.format(repo=repo)
        else:
            project = mapping[repo]
            artifactId = project['artifactId']
            name = project['name']
            if project['description']:
                description = project['description'].replace('\n', ' ')
            else:
                description = ''
            row = '[{repo}](https://github.com/apache/{repo})|`{artifactId}`|{name}|{description}'.format(repo=repo, artifactId=artifactId, name=name, description=description)
        markdown.append(row)
    return '\n'.join(markdown)


def write_text_file(text, filename):
    with open(filename, 'w') as f:
        f.write(text)


def write_xml_file(element, filename):
    s = xml.etree.ElementTree.tostring(element, 'UTF-8')
    document = xml.dom.minidom.parseString(s)
    with open(filename, 'w') as f:
        document.writexml(f, indent='', addindent='  ', newl='\n', encoding='UTF-8')
    document.unlink()


def build():
    opml = read_opml()
    repos = filter_sling_repos(opml)
    mapping = map_projects(repos)
    manifest = build_repo_manifest(mapping)
    write_xml_file(manifest, 'default.xml')
    pom = build_maven_aggregator_pom(mapping)
    write_xml_file(pom, 'pom.xml')
    index = build_index_markdown(mapping)
    write_text_file(index, 'index.md')


if __name__ == '__main__':
    build()

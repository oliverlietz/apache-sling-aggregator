#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.request
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


def read_artifact_id(pom):
    artifactId = pom.findall('./{http://maven.apache.org/POM/4.0.0}artifactId')[0].text
    return artifactId.strip()


def map_artifact_ids(repos):
    mapping = {}
    for repo in repos:
        pom = read_pom(repo)
        if pom:
            mapping[repo] = read_artifact_id(pom)
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
        path = repo if mapping[repo] is None else mapping[repo]
        project = xml.etree.ElementTree.Element('project')
        project.set('path', path)
        project.set('name', repo)
        project.set('remote', 'origin')
        manifest.append(project)

    return xml.etree.ElementTree.ElementTree(manifest)


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
    artifactIds = sorted(filter(None, mapping.values()))
    for artifactId in artifactIds:
        if artifactId not in maven_blacklist:
            module = xml.etree.ElementTree.Element('module')
            module.text = artifactId
            modules.append(module)

    build = build_pom_build()
    pom.append(build)
    return xml.etree.ElementTree.ElementTree(pom)


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


def build():
    opml = read_opml()
    repos = filter_sling_repos(opml)
    mapping = map_artifact_ids(repos)
    manifest = build_repo_manifest(mapping)
    manifest.write('default.xml', encoding='utf-8')
    pom = build_maven_aggregator_pom(mapping)
    pom.write('pom.xml', encoding='utf-8')


if __name__ == '__main__':
    build()

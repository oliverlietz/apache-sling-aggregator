#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.request
import xml.etree.ElementTree

blacklist = ['sling-aggregator', 'sling-tooling-jenkins', 'sling-tooling-release', 'sling-tooling-scm', 'sling-whiteboard']


def read_opml():
    response = urllib.request.urlopen('https://gitbox.apache.org/repos/asf?a=opml')
    return response.read()


def read_pom(repo):
    url = 'https://gitbox.apache.org/repos/asf?p=%s.git;a=blob_plain;f=pom.xml;hb=HEAD' % (repo)
    response = urllib.request.urlopen(url)
    return response.read()


def filter_sling_repos(opml):
    repos = []
    root = xml.etree.ElementTree.fromstring(opml)
    result = root.findall(".//outline[@xmlUrl]")
    pattern = re.compile('p=(.*)\.git')
    for element in result:
        xmlUrl = element.attrib['xmlUrl']
        if xmlUrl.startswith('https://gitbox.apache.org/repos/asf?p=sling-'):
            urls = re.findall(pattern, xmlUrl)
            if len(urls) == 1:
                url = urls[0]
                if url not in blacklist:
                    repos.append(url)
    repos.sort()
    return repos


def read_artifact_id(pom):
    root = xml.etree.ElementTree.fromstring(pom)
    artifactId = root.findall('./{http://maven.apache.org/POM/4.0.0}artifactId')[0].text
    return artifactId.strip()


def map_artifact_ids(repos):
    mapping = {}
    for repo in repos:
        pom = read_pom(repo)
        artifactId = read_artifact_id(pom)
        if artifactId:
            mapping[artifactId] = repo
    return mapping


def build_repo_manifest(mapping):
    manifest = xml.etree.ElementTree.Element('manifest')
    manifest.append(build_remote('origin', 'https://gitbox.apache.org/repos/asf/', 'master'))
    manifest.append(build_remote('oliverlietz', 'https://github.com/oliverlietz/', 'master'))
    project = xml.etree.ElementTree.Element('project')
    project.set('path', '.')
    project.set('name', 'apache-sling-aggregator')
    project.set('remote', 'oliverlietz')
    manifest.append(project)
    for artifactId in sorted(mapping):
        project = xml.etree.ElementTree.Element('project')
        project.set('path', artifactId)
        project.set('name', mapping[artifactId])
        project.set('remote', 'origin')
        manifest.append(project)

    return xml.etree.ElementTree.ElementTree(manifest)


def build_remote(name, fetch, revision):
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

    parent = build_parent()
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
    for artifactId in sorted(mapping):
        module = xml.etree.ElementTree.Element('module')
        module.text = artifactId
        modules.append(module)

    return xml.etree.ElementTree.ElementTree(pom)


def build_parent():
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

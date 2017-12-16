# Apache Sling – Aggregator

[Maven aggregator project](https://maven.apache.org/pom.html#Aggregation) for [Apache Sling](https://sling.apache.org)

Install [Google Repo](https://source.android.com/setup/using-repo) on Mac OS with [Homebrew](https://brew.sh):

	brew install repo

Setup [Google Repo](https://source.android.com/setup/using-repo) and clone Sling's modules from [GitBox](https://gitbox.apache.org/repos/asf):

    repo init --no-clone-bundle --config-name -u https://github.com/oliverlietz/apache-sling-aggregator.git -b repo
    repo sync --no-clone-bundle -j 16
    repo forall -c git checkout master
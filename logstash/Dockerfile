FROM docker.elastic.co/logstash/logstash:7.16.3

# Install Logstash plugins
RUN bin/logstash-plugin install logstash-input-cloudwatch_logs
RUN bin/logstash-plugin install logstash-output-elasticsearch

# Copy Logstash configuration file
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

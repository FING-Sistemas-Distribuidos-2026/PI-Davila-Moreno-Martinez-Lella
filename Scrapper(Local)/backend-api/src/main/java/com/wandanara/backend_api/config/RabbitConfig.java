package com.wandanara.backend_api.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.JacksonJsonMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitConfig {

    public static final String SCRAPING_QUEUE = "scraping.jobs";
    public static final String RESULTS_QUEUE = "scraping.results";
    public static final String RETRY_QUEUE = "scraping.jobs.retry";
    public static final String DLQ_QUEUE = "scraping.jobs.dlq";

    @Bean
    public Queue scrapingQueue() {
        return QueueBuilder.durable(SCRAPING_QUEUE).build();
    }

    @Bean
    public Queue resultsQueue() {
        return QueueBuilder.durable(RESULTS_QUEUE).build();
    }

    @Bean
    public Queue retryQueue() {
        return QueueBuilder.durable(RETRY_QUEUE)
                .ttl(5000)
                .deadLetterExchange("")
                .deadLetterRoutingKey(SCRAPING_QUEUE)
                .build();
    }

    @Bean
    public Queue dlqQueue() {
        return QueueBuilder.durable(DLQ_QUEUE).build();
    }

    @Bean
    public JacksonJsonMessageConverter jsonMessageConverter() {
        return new JacksonJsonMessageConverter();
    }

    @Bean
    public RabbitTemplate rabbitTemplate(
            ConnectionFactory connectionFactory,
            JacksonJsonMessageConverter jsonMessageConverter
    ) {
        RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
        rabbitTemplate.setMessageConverter(jsonMessageConverter);
        return rabbitTemplate;
    }
}
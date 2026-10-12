FROM maven:3.9.12-eclipse-temurin-21 AS build
WORKDIR /src
COPY services/forecasts/pom.xml ./
COPY services/forecasts/src ./src
RUN mvn -B package -DskipTests
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/forecasts-0.1.0.jar ./app.jar
COPY contracts /app/contracts
COPY fixtures /app/fixtures
ENTRYPOINT ["java","-jar","app.jar"]

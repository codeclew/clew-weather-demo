FROM mcr.microsoft.com/dotnet/sdk:10.0.401 AS build
WORKDIR /src
COPY services/places ./
RUN dotnet publish Places.csproj -c Release -o /publish
FROM mcr.microsoft.com/dotnet/aspnet:10.0.12
WORKDIR /app
COPY --from=build /publish ./
COPY contracts /app/contracts
ENV ASPNETCORE_URLS=http://+:8080
ENTRYPOINT ["dotnet","Places.dll"]

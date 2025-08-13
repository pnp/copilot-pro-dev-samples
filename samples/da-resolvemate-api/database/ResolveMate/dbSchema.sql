-- Drop Tables if they already exist to ensure a clean setup
IF OBJECT_ID('dbo.Resolutions', 'U') IS NOT NULL DROP TABLE Resolutions;
IF OBJECT_ID('dbo.Tickets', 'U') IS NOT NULL DROP TABLE Tickets;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE Products;
IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL DROP TABLE Customers;

-- 1. Create Database
--CREATE DATABASE CustomerSupportDB;
--GO

USE [db-resolvemate];
GO

-- 2. Create Tables

-- Table: Customers
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY IDENTITY(1,1),
    CustomerName VARCHAR(100) NOT NULL,
    CustomerEmail VARCHAR(255) NOT NULL UNIQUE,
    CustomerAge VARCHAR(10),
    CustomerGender VARCHAR(10)
);
GO

-- Table: Products
CREATE TABLE Products (
    ProductID INT PRIMARY KEY IDENTITY(1,1),
    ProductName VARCHAR(100) NOT NULL,    
    ProductCategory VARCHAR(50),
    PurchasedDate DATETIME

);
GO

-- Table: Tickets
CREATE TABLE Tickets (
    TicketID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID INT NOT NULL,
    ProductID INT,
    TicketType VARCHAR(50),
    TicketSubject VARCHAR(255),
    TicketDescription TEXT,
    TicketStatus VARCHAR(50),
    TicketPriority VARCHAR(20),
    TicketChannel VARCHAR(50),
    FirstResponseTime DATETIME,
    TimeToResolution DATETIME,
    CustomerSatisfactionRating FLOAT,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);
GO

-- Table: Resolutions
CREATE TABLE Resolutions (
    ResolutionID INT PRIMARY KEY IDENTITY(1,1),
    TicketID INT NOT NULL,
    Resolution TEXT,
    ResolutionDate DATETIME,
    FOREIGN KEY (TicketID) REFERENCES Tickets(TicketID)
);
GO

-- 3. Indexes

-- Index for searching tickets by TicketID
CREATE INDEX idx_ticket_id ON Tickets (TicketID);
GO

-- Index for searching tickets by status and priority
CREATE INDEX idx_ticket_status_priority ON Tickets (TicketStatus, TicketPriority);
GO

-- Drop Full-Text Catalog if it exists to avoid conflicts
IF EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'ftCatalog')
    DROP FULLTEXT CATALOG ftCatalog;
GO

-- Create Full-Text Catalog
CREATE FULLTEXT CATALOG ftCatalog AS DEFAULT;
GO

-- Create a unique index on TicketID specifically for full-text key
CREATE UNIQUE INDEX idx_ticket_fulltext_key ON Tickets(TicketID);
GO

-- Create Full-Text Index on TicketSubject and TicketDescription
CREATE FULLTEXT INDEX ON Tickets (TicketSubject, TicketDescription)
    KEY INDEX idx_ticket_fulltext_key;
GO

-- 4. Stored Procedures

-- Get Tickets by ID
CREATE PROCEDURE GetTicketByID
    @TicketID INT
AS
BEGIN
    SELECT * FROM Tickets WHERE TicketID = @TicketID;
END;
GO

-- Get Tickets by Status and Priority
CREATE PROCEDURE GetTicketsByStatusPriority
    @TicketStatus VARCHAR(50),
    @TicketPriority VARCHAR(20)
AS
BEGIN
    SELECT * FROM Tickets 
    WHERE TicketStatus = @TicketStatus 
      AND TicketPriority = @TicketPriority;
END;
GO

-- Search Tickets by Subject and Description
CREATE PROCEDURE SearchTickets
    @SearchTerm NVARCHAR(255)
AS
BEGIN
    SELECT * FROM Tickets
    WHERE CONTAINS(TicketSubject, @SearchTerm) 
       OR CONTAINS(TicketDescription, @SearchTerm);
END;
GO

-- Update Ticket
CREATE PROCEDURE UpdateTicket
    @TicketID INT,
    @TicketStatus VARCHAR(50),
    @TicketPriority VARCHAR(20),
    @CustomerSatisfactionRating FLOAT = NULL
AS
BEGIN
    UPDATE Tickets
    SET TicketStatus = @TicketStatus,
        TicketPriority = @TicketPriority,
        CustomerSatisfactionRating = @CustomerSatisfactionRating
    WHERE TicketID = @TicketID;
END;
GO
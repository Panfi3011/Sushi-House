-- Ejecutar este archivo en SQL Server Management Studio (SSMS).
-- Crea la base y las tablas para usuarios y reservas.
IF DB_ID(N'sushi_house') IS NULL
BEGIN
    CREATE DATABASE sushi_house;
END;
GO

USE sushi_house;
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        email NVARCHAR(254) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_users_created_at DEFAULT SYSDATETIME()
    );
END;
GO

IF OBJECT_ID(N'dbo.reservations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.reservations (
        id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        reservation_at DATETIME2 NOT NULL,
        guests TINYINT NOT NULL,
        notes NVARCHAR(500) NULL,
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_reservations_status DEFAULT N'confirmed',
        created_at DATETIME2 NOT NULL CONSTRAINT DF_reservations_created_at DEFAULT SYSDATETIME(),
        CONSTRAINT FK_reservations_users FOREIGN KEY (user_id) REFERENCES dbo.users(id),
        CONSTRAINT CK_reservations_guests CHECK (guests BETWEEN 1 AND 12),
        CONSTRAINT CK_reservations_status CHECK (status IN (N'confirmed', N'cancelled'))
    );
    CREATE INDEX IX_reservations_user_date ON dbo.reservations(user_id, reservation_at);
END;
GO

-- Relación: un usuario puede tener muchas reservas. Cada reserva pertenece a un usuario.
SELECT name FROM sys.tables WHERE name IN (N'users', N'reservations');
GO

USE sushi_house;
SELECT * FROM dbo.users;
SELECT * FROM dbo.reservations;
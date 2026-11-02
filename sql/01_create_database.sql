-- SQL Server 2017+. Review the target name before executing manually.
USE [master];
GO
IF DB_ID(N'VietCommerce') IS NULL
    EXEC(N'CREATE DATABASE [VietCommerce]');
GO

using CommerceLab.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace CommerceLab.Data;

public sealed class CommerceDbContext(DbContextOptions<CommerceDbContext> options)
    : DbContext(options)
{
    public DbSet<Customer> Customers => Set<Customer>();

    public DbSet<Product> Products => Set<Product>();

    public DbSet<Stock> Stocks => Set<Stock>();

    public DbSet<Order> Orders => Set<Order>();

    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    public DbSet<Payment> Payments => Set<Payment>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Customer>(entity =>
        {
            entity.ToTable("Customers", "sales");
            entity.HasKey(x => x.CustomerId);
            entity.Property(x => x.Email).HasMaxLength(320).IsUnicode(false);
            entity.Property(x => x.FullName).HasMaxLength(120);
            entity.HasIndex(x => x.Email).IsUnique();
        });

        modelBuilder.Entity<Product>(entity =>
        {
            entity.ToTable("Products", "catalog");
            entity.HasKey(x => x.ProductId);
            entity.Property(x => x.Sku).HasMaxLength(40).IsUnicode(false);
            entity.Property(x => x.Name).HasMaxLength(160);
            entity.Property(x => x.Price).HasPrecision(19, 4);
            entity.HasIndex(x => x.Sku).IsUnique();
            entity.HasQueryFilter("ActiveProductFilter", x => x.IsActive);
        });

        modelBuilder.Entity<Stock>(entity =>
        {
            entity.ToTable("Stock", "inventory");
            entity.HasKey(x => x.ProductId);
            entity.HasOne(x => x.Product)
                .WithOne()
                .HasForeignKey<Stock>(x => x.ProductId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<Order>(entity =>
        {
            entity.ToTable("Orders", "sales");
            entity.HasKey(x => x.OrderId);
            entity.Property(x => x.Status).HasMaxLength(20).IsUnicode(false);
            entity.Property(x => x.ShippingName).HasMaxLength(120);
            entity.Property(x => x.ShippingAddress).HasMaxLength(500);
            entity.Property(x => x.TotalAmount).HasPrecision(19, 4);
            entity.Property(x => x.ConcurrencyToken).IsConcurrencyToken();
            entity.HasIndex(x => new { x.CustomerId, x.OrderedAt });
            entity.HasOne(x => x.Customer)
                .WithMany(x => x.Orders)
                .HasForeignKey(x => x.CustomerId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<OrderItem>(entity =>
        {
            entity.ToTable("OrderItems", "sales");
            entity.HasKey(x => x.OrderItemId);
            entity.Property(x => x.ProductNameSnapshot).HasMaxLength(160);
            entity.Property(x => x.UnitPriceSnapshot).HasPrecision(19, 4);
            entity.HasIndex(x => new { x.OrderId, x.ProductId }).IsUnique();
            entity.HasOne(x => x.Order)
                .WithMany(x => x.Items)
                .HasForeignKey(x => x.OrderId)
                .OnDelete(DeleteBehavior.Cascade);
            entity.HasOne(x => x.Product)
                .WithMany(x => x.OrderItems)
                .HasForeignKey(x => x.ProductId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<Payment>(entity =>
        {
            entity.ToTable("Payments", "billing");
            entity.HasKey(x => x.PaymentId);
            entity.Property(x => x.Provider).HasMaxLength(30).IsUnicode(false);
            entity.Property(x => x.ProviderReference).HasMaxLength(100).IsUnicode(false);
            entity.Property(x => x.Status).HasMaxLength(20).IsUnicode(false);
            entity.Property(x => x.Amount).HasPrecision(19, 4);
            entity.HasIndex(x => new { x.OrderId, x.CreatedAt });
            entity.HasOne(x => x.Order)
                .WithMany(x => x.Payments)
                .HasForeignKey(x => x.OrderId)
                .OnDelete(DeleteBehavior.Restrict);
        });
    }
}

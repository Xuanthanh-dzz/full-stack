# Covariance và contravariance

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích generic type invariant, covariant và contravariant;
- đọc đúng ý nghĩa `out T` trên producer và `in T` trên consumer;
- thực hiện variance conversion an toàn giữa các interface/delegate reference type;
- hiểu conversion chỉ tạo view API mới, không clone object;
- phân biệt variance của generic interface/delegate với array covariance;
- nhận ra variance conversion không áp dụng tương tự cho value type;
- thiết kế API nhỏ theo hướng producer/consumer;
- tránh dùng cast để che một generic contract sai.

## 2. Bài toán mở đầu

Hệ thống nhận nuôi động vật có một nguồn chỉ tạo `Cat` và một nơi ghi log chấp nhận mọi `Animal`. Ta muốn:

- dùng nguồn `Cat` ở nơi chỉ yêu cầu nguồn `Animal`;
- dùng logger `Animal` ở nơi chỉ gửi `Cat`;
- không cho code đưa `Dog` vào storage chỉ dành cho `Cat`;
- không copy object chỉ để đổi góc nhìn generic.

Nếu mọi `Generic<Cat>` tự động được coi là `Generic<Animal>`, một API vừa đọc vừa ghi có thể phá type safety. Variance chỉ hợp lệ khi hướng dữ liệu trong contract đủ rõ.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name VarianceDemo --framework net9.0 --use-program-main
cd VarianceDemo
```

Thay `VarianceDemo.csproj` bằng:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

Thay `Program.cs` bằng:

```csharp
namespace VarianceDemo;

internal static class Program
{
    private static void Main()
    {
        ISource<Cat> cats = new SingleValueSource<Cat>(new Cat("Milo"));

        // Covariance: nguồn Cat dùng được như nguồn Animal.
        ISource<Animal> animals = cats;
        Animal received = animals.Next();
        Console.WriteLine(
            $"Covariant source: {received.Name} ({received.GetType().Name})");

        ISink<Animal> animalLog = new AnimalConsoleSink();

        // Contravariance: nơi nhận mọi Animal chắc chắn nhận được Cat.
        ISink<Cat> catLog = animalLog;
        catLog.Write(new Cat("Luna"));

        // Func có TResult covariant.
        Func<Cat> createCat = () => new Cat("Simba");
        Func<Animal> createAnimal = createCat;
        Console.WriteLine($"Covariant Func: {createAnimal().Name}");

        // Action có parameter contravariant.
        Action<Animal> describeAnimal = animal =>
            Console.WriteLine($"Action handled: {animal.Name}");
        Action<Cat> describeCat = describeAnimal;
        describeCat(new Cat("Nori"));
    }
}

internal interface ISource<out T>
{
    T Next();
}

internal interface ISink<in T>
{
    void Write(T value);
}

internal sealed class SingleValueSource<T> : ISource<T>
{
    private readonly T _value;

    public SingleValueSource(T value)
    {
        _value = value;
    }

    public T Next() => _value;
}

internal sealed class AnimalConsoleSink : ISink<Animal>
{
    public void Write(Animal value)
    {
        Console.WriteLine(
            $"Contravariant sink: {value.Name} ({value.GetType().Name})");
    }
}

internal abstract record Animal(string Name);

internal sealed record Cat(string Name) : Animal(Name);

internal sealed record Dog(string Name) : Animal(Name);
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
Covariant source: Milo (Cat)
Contravariant sink: Luna (Cat)
Covariant Func: Simba
Action handled: Nori
```

## 4. Giải thích cơ chế

### 4.1. Covariance giữ hướng kế thừa

`Cat` là `Animal`. `ISource<out T>` chỉ phát giá trị `T`, nên nguồn chỉ tạo `Cat` có thể đáp ứng nơi cần nhận một `Animal`:

```text
Cat ------------------------------------> Animal
ISource<Cat> -- variance conversion ---> ISource<Animal>
```

`out` nằm ở declaration của type parameter, không nằm tại phép gán. Compiler kiểm tra `T` chỉ xuất hiện ở vị trí output hợp lệ trong interface. `T Next()` hợp lệ; `void Add(T value)` sẽ không compile trong `ISource<out T>` vì đó là input.

### 4.2. Contravariance đảo hướng generic conversion

`ISink<Animal>` nhận được mọi `Animal`, nên chắc chắn nhận được `Cat`. Vì vậy nó dùng được ở nơi cần `ISink<Cat>`:

```text
Cat ------------------------------------> Animal
ISink<Cat> <--- variance conversion ---- ISink<Animal>
```

Hướng mũi tên của constructed generic type bị đảo. `in T` cho phép `T` ở vị trí input như `Write(T)`. Nếu interface trả `T`, caller của `ISink<Cat>` có thể đòi một `Cat` trong khi implementation chỉ hứa một `Animal`; compiler vì thế từ chối output đó.

### 4.3. Conversion không tạo object mới

Sau hai assignment đầu, graph là:

```text
STACK / REGISTERS
cats    = ref S1 ──┐
animals = ref S1 ──┘

MANAGED HEAP
S1 SingleValueSource<Cat>
└── _value = ref C1 ----> C1 Cat { Name: "Milo" }
```

Không có `new` tại `ISource<Animal> animals = cats;`, nên không có source hoặc `Cat` mới. Runtime/reference conversion chỉ cho biến `animals` một API view `ISource<Animal>`. Object thực vẫn là `SingleValueSource<Cat>`.

Tương tự, `animalLog` và `catLog` cùng trỏ một `AnimalConsoleSink`. Variance không deep-copy, không đổi runtime type và không thay ownership.

### 4.4. Tại sao `List<Cat>` không phải `List<Animal>`?

`List<T>` vừa đọc vừa ghi `T`, nên invariant. Nếu phép gán sau được phép:

```csharp
// Không compile — và đó là điều đúng.
List<Cat> cats = new();
List<Animal> animals = cats;
animals.Add(new Dog("Rex"));
```

storage `List<Cat>` sẽ chứa `Dog`, phá contract. Khi cần view chỉ đọc, dùng một interface covariant phù hợp; khi cần ghi, chọn consumer contravariant hoặc copy có chủ đích sang collection khác.

### 4.5. Delegate dùng cùng quy tắc hướng dữ liệu

Khai báo framework có ý tưởng tương đương:

```csharp
public delegate TResult Func<out TResult>();
public delegate void Action<in T>(T value);
```

Hàm tạo `Cat` dùng được như hàm tạo `Animal`; handler biết xử lý mọi `Animal` dùng được như handler chỉ được gửi `Cat`. Delegate object không chạy trong lúc conversion; nó chỉ chạy khi gọi `Invoke`/`()`.

## 5. Kiến thức nền

### Invariant, covariant, contravariant

| Dạng | Marker | Hướng conversion với `Cat : Animal` | Vai trò điển hình |
|---|---|---|---|
| invariant | không có | không conversion giữa hai constructed type | đọc và ghi |
| covariant | `out T` | `G<Cat> → G<Animal>` | producer/read-only view |
| contravariant | `in T` | `G<Animal> → G<Cat>` | consumer/comparer/handler |

Tên `in`/`out` mô tả vị trí type parameter trong contract, không phải modifier truyền parameter `in`/`out` của method ở bài 04.

### Type nào khai báo variance?

C# cho phép variance annotation trên generic interface và generic delegate. Generic class/struct không khai báo `out T` hoặc `in T`; class có thể implement một interface variant để cung cấp view an toàn.

Các ví dụ framework:

- `IEnumerable<out T>` phát phần tử;
- `IComparer<in T>` nhận hai giá trị để so sánh;
- `Func<in T, out TResult>` nhận input và phát result;
- `Action<in T>` nhận input.

### Chỉ có variance conversion cho reference type argument

`ISource<int>` không variance-convert thành `ISource<object>`. `int` là value type; muốn thành `object` cần boxing từng value, không phải cùng reference representation của constructed interface. Với `string` và `object`, conversion covariant có thể áp dụng vì cả hai là reference type.

### Array covariance là di sản có runtime check

C# cho phép:

```csharp
Animal[] animals = new Cat[1];
```

nhưng `animals[0] = new Dog("Rex")` compile rồi ném `ArrayTypeMismatchException` ở runtime. Generic variance được thiết kế để loại hành vi ghi nguy hiểm khỏi contract ở compile time; đừng dùng array covariance như mẫu thiết kế API.

### Variance và inheritance là hai việc khác nhau

`SingleValueSource<Cat>` implement `ISource<Cat>`. Nó không kế thừa `SingleValueSource<Animal>`. Conversion xảy ra giữa hai constructed interface type nhờ `out T`, không tạo quan hệ kế thừa mới giữa hai class generic.

## 6. Lỗi thường gặp

### Nhớ hướng bằng câu chữ nhưng không vẽ input/output

Dễ đảo contravariance. Hãy viết method contract: type được trả ra hay được đưa vào? Sau đó thử một `Dog` để kiểm tra type safety.

### Cho `out T` vào parameter input

Compiler từ chối vì caller qua view rộng hơn có thể đưa subtype không phù hợp vào implementation. Tách producer và consumer thay vì ép một interface làm cả hai.

### Cast `List<Cat>` thành `List<Animal>`

Cast không biến storage thành collection an toàn. Nếu cần list mới, tạo và copy có chủ đích; nếu chỉ đọc, nhận interface read-only covariant thích hợp.

### Nhầm method `out` với generic `out`

`out decimal total` là truyền storage output cho một lời gọi. `ISource<out T>` là variance annotation trên type parameter. Cùng keyword, hai cơ chế khác nhau.

### Quên giới hạn reference type của conversion

Viết API dựa trên giả định `G<int> → G<object>` sẽ thất bại. Xử lý value type bằng generic code trực tiếp hoặc boxing tường minh nếu contract thực sự cần object.

### Lạm dụng interface nhỏ không có nhu cầu thay thế

Variance có ích khi có consumer thực sự cần view rộng/hẹp. Không tạo nhiều abstraction chỉ để sử dụng `in/out`; giữ API đơn giản và kiểm thử use case thay thế thật.

## 7. Bài tập

### Bài 1 — Nguồn thông báo

Tạo `Message`, `EmailMessage : Message` và `ISource<out T>`. Dùng source email như source message.

**Gợi ý:** interface chỉ nên trả `T`; vẽ hai reference cùng trỏ source object.

### Bài 2 — Handler contravariant

Tạo `IHandler<in T>` với `Handle(T value)`. Dùng handler `Message` ở nơi yêu cầu handler `EmailMessage`.

**Gợi ý:** thử chiều ngược lại và giải thích vì sao không an toàn.

### Bài 3 — Tìm lỗi của collection

Giải thích bằng code vì sao `List<Dog>` không gán được cho `List<Animal>`, sau đó chọn một read-only view hoặc tạo list mới.

**Gợi ý:** thử tưởng tượng caller thêm `Cat` qua biến `List<Animal>`.

### Bài 4 — Delegate hai chiều

Tạo `Func<Animal, Cat>` rồi khảo sát assignment nào hợp lệ với `Func<Cat, Animal>`.

**Gợi ý:** phân tích parameter là `in`, result là `out`; kiểm tra từng hướng riêng trước khi kết hợp.

### Bài 5 — Value type

Thử gán `ISource<int>` sang `ISource<object>`, ghi lỗi compile và viết adapter box từng `int` có chủ đích.

**Gợi ý:** adapter là object mới thực hiện `ISource<object>`; variance conversion đơn thuần không boxing phần tử.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi xác định được `T` đang đi vào hay đi ra contract.
- [ ] Tôi vẽ đúng hướng covariance và contravariance.
- [ ] Tôi biết variance conversion không tạo object mới.
- [ ] Tôi giải thích được vì sao type vừa đọc vừa ghi thường invariant.
- [ ] Tôi phân biệt generic variance, method parameter modifier và array covariance.
- [ ] Tôi nhớ variance conversion chỉ áp dụng với reference type argument.

Điều hướng:

- Prerequisite: [`Span<T>`, `Memory<T>` và lập trình hiệu năng](./14-span-memory-va-lap-trinh-hieu-nang.md)
- Bài tiếp theo: [Expression tree](./16-expression-tree.md)

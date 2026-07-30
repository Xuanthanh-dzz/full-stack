# Dự án console C#: trình quản lý công việc có lưu JSON

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Ghép biến, method, class, interface, enum, collection và exception thành một chương trình hoàn chỉnh.
- Tách code theo trách nhiệm: giao diện dòng lệnh, nghiệp vụ, domain và lưu trữ.
- Thêm, liệt kê, hoàn thành và xóa công việc bằng command-line argument.
- Lưu dữ liệu JSON an toàn hơn bằng cách ghi file tạm rồi thay thế file chính.
- Build và chạy một project `net9.0` chỉ bằng .NET CLI.
- Giải thích object nào được tạo bởi từng lần `new`, reference nào giữ object và dữ liệu sống bao lâu.

## 2. Bài toán mở đầu

Bạn cần một chương trình quản lý việc cá nhân chạy được trong terminal. Dữ liệu không được mất sau khi process kết thúc. Các lệnh cần hỗ trợ là:

```text
add "Hoc C#"
list
done 1
remove 1
```

Một cách làm nhanh là đặt toàn bộ menu, `List<TodoItem>` và thao tác file vào `Program.cs`. Cách đó vẫn chạy, nhưng sớm phát sinh ba vấn đề:

1. Code đọc command-line trộn với rule nghiệp vụ nên khó kiểm tra.
2. Bất kỳ phần nào cũng có thể sửa trực tiếp trạng thái của công việc.
3. Nếu ghi đè `tasks.json` bị gián đoạn, file chính có thể hỏng.

Ta sẽ giải bài toán bằng một project duy nhất nhưng chia namespace và thư mục theo trách nhiệm. Đây chưa phải kiến trúc nhiều tầng hoàn chỉnh; mục tiêu là tạo ranh giới code rõ ràng bằng đúng kiến thức C# cơ bản.

### Tiêu chí chấp nhận

- Title rỗng hoặc chỉ có khoảng trắng bị từ chối.
- `done` và `remove` báo rõ khi không tìm thấy ID.
- Mỗi thay đổi hợp lệ được lưu ngay vào JSON.
- `list` hoạt động cả khi chưa có file dữ liệu.
- Không truyền command được coi là yêu cầu help và trả `0`; command/argument sai trả mã khác `0`.
- Lỗi dự kiến không làm xuất hiện stack trace khó hiểu với người dùng cuối.

## 3. Lời giải bằng code

### 3.1 Tạo project

Yêu cầu: .NET SDK 9.x. Kiểm tra và tạo project:

```bash
dotnet --version
mkdir TaskManager
cd TaskManager
dotnet new console --framework net9.0
mkdir -p Domain Application Infrastructure
```

Thay nội dung file project bằng cấu hình sau.

`TaskManager.csproj`:

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

### 3.2 Domain: trạng thái và object công việc

`Domain/TodoStatus.cs`:

```csharp
namespace TaskManager.Domain;

public enum TodoStatus
{
    Pending = 0,
    Completed = 1
}
```

`Domain/TodoItem.cs`:

```csharp
namespace TaskManager.Domain;

public sealed class TodoItem
{
    public int Id { get; }
    public string Title { get; private set; }
    public TodoStatus Status { get; private set; }
    public DateTimeOffset CreatedAt { get; }

    public TodoItem(
        int id,
        string title,
        TodoStatus status,
        DateTimeOffset createdAt)
    {
        if (id <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(id), "Id phải lớn hơn 0.");
        }

        if (!Enum.IsDefined(status))
        {
            throw new ArgumentOutOfRangeException(
                nameof(status), "Trạng thái công việc không hợp lệ.");
        }

        Id = id;
        Title = NormalizeTitle(title);
        Status = status;
        CreatedAt = createdAt;
    }

    public void Rename(string newTitle)
    {
        Title = NormalizeTitle(newTitle);
    }

    public void MarkCompleted()
    {
        Status = TodoStatus.Completed;
    }

    private static string NormalizeTitle(string title)
    {
        ArgumentNullException.ThrowIfNull(title);

        string normalized = title.Trim();
        if (normalized.Length == 0)
        {
            throw new ArgumentException(
                "Tiêu đề không được để trống.", nameof(title));
        }

        if (normalized.Length > 200)
        {
            throw new ArgumentException(
                "Tiêu đề không được vượt quá 200 ký tự.", nameof(title));
        }

        return normalized;
    }
}
```

### 3.3 Abstraction lưu trữ và service nghiệp vụ

`Application/ITodoRepository.cs`:

```csharp
using TaskManager.Domain;

namespace TaskManager.Application;

public interface ITodoRepository
{
    List<TodoItem> Load();
    void Save(IReadOnlyCollection<TodoItem> items);
}
```

`Application/TodoItemView.cs`:

```csharp
using TaskManager.Domain;

namespace TaskManager.Application;

// Read model không có API mutation và không làm lộ TodoItem do service quản lý.
public sealed class TodoItemView
{
    public int Id { get; }
    public string Title { get; }
    public TodoStatus Status { get; }
    public DateTimeOffset CreatedAt { get; }

    internal TodoItemView(TodoItem item)
    {
        Id = item.Id;
        Title = item.Title;
        Status = item.Status;
        CreatedAt = item.CreatedAt;
    }
}
```

`Application/TodoService.cs`:

```csharp
using TaskManager.Domain;

namespace TaskManager.Application;

public sealed class TodoService
{
    private readonly ITodoRepository _repository;
    private readonly List<TodoItem> _items;

    public TodoService(ITodoRepository repository)
    {
        _repository = repository
            ?? throw new ArgumentNullException(nameof(repository));
        _items = repository.Load();
    }

    public IReadOnlyList<TodoItemView> GetAll()
    {
        // Tạo snapshot read model; caller không nhận mutable TodoItem gốc.
        var result = new List<TodoItemView>(_items.Count);
        foreach (TodoItem item in _items)
        {
            result.Add(new TodoItemView(item));
        }

        return result.AsReadOnly();
    }

    public TodoItemView Add(string title)
    {
        var item = new TodoItem(
            GetNextId(),
            title,
            TodoStatus.Pending,
            DateTimeOffset.UtcNow);

        _items.Add(item);
        _repository.Save(_items);
        return new TodoItemView(item);
    }

    public bool MarkCompleted(int id)
    {
        TodoItem? item = FindById(id);
        if (item is null)
        {
            return false;
        }

        item.MarkCompleted();
        _repository.Save(_items);
        return true;
    }

    public bool Remove(int id)
    {
        TodoItem? item = FindById(id);
        if (item is null)
        {
            return false;
        }

        _items.Remove(item);
        _repository.Save(_items);
        return true;
    }

    private TodoItem? FindById(int id)
    {
        foreach (TodoItem item in _items)
        {
            if (item.Id == id)
            {
                return item;
            }
        }

        return null;
    }

    private int GetNextId()
    {
        int maxId = 0;
        foreach (TodoItem item in _items)
        {
            if (item.Id > maxId)
            {
                maxId = item.Id;
            }
        }

        return checked(maxId + 1);
    }
}
```

### 3.4 Infrastructure: lưu JSON qua file tạm

`Infrastructure/JsonTodoRepository.cs`:

```csharp
using System.Text.Json;
using TaskManager.Application;
using TaskManager.Domain;

namespace TaskManager.Infrastructure;

public sealed class JsonTodoRepository : ITodoRepository
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true
    };

    private readonly string _filePath;

    public JsonTodoRepository(string filePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(filePath);
        _filePath = Path.GetFullPath(filePath);
    }

    public List<TodoItem> Load()
    {
        if (!File.Exists(_filePath))
        {
            return [];
        }

        try
        {
            string json = File.ReadAllText(_filePath);
            List<TodoDocument?> documents =
                JsonSerializer.Deserialize<List<TodoDocument?>>(
                    json, JsonOptions) ?? [];

            var items = new List<TodoItem>(documents.Count);
            foreach (TodoDocument? document in documents)
            {
                if (document is null)
                {
                    throw new InvalidDataException(
                        $"Danh sách JSON chứa phần tử null: {_filePath}");
                }

                items.Add(new TodoItem(
                    document.Id,
                    document.Title,
                    document.Status,
                    document.CreatedAt));
            }

            return items;
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException(
                $"File JSON không hợp lệ: {_filePath}", exception);
        }
        catch (ArgumentException exception)
        {
            // JSON đúng cú pháp nhưng vi phạm invariant domain.
            throw new InvalidDataException(
                $"Dữ liệu công việc không hợp lệ: {_filePath}", exception);
        }
    }

    public void Save(IReadOnlyCollection<TodoItem> items)
    {
        string? directory = Path.GetDirectoryName(_filePath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var documents = new List<TodoDocument>(items.Count);
        foreach (TodoItem item in items)
        {
            documents.Add(new TodoDocument
            {
                Id = item.Id,
                Title = item.Title,
                Status = item.Status,
                CreatedAt = item.CreatedAt
            });
        }

        string json = JsonSerializer.Serialize(documents, JsonOptions);
        string temporaryPath = _filePath + ".tmp";

        try
        {
            File.WriteAllText(temporaryPath, json);
            File.Move(temporaryPath, _filePath, overwrite: true);
        }
        finally
        {
            // Dọn file tạm nếu ghi hoặc thay thế thất bại.
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }

    private sealed class TodoDocument
    {
        public int Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public TodoStatus Status { get; set; }
        public DateTimeOffset CreatedAt { get; set; }
    }
}
```

`TodoDocument` là kiểu dành riêng cho serialization. Domain object `TodoItem` vẫn bảo vệ invariant bằng constructor và `private set`.

### 3.5 Giao diện dòng lệnh

Thay toàn bộ file sau.

`Program.cs`:

```csharp
using System.Globalization;
using TaskManager.Application;
using TaskManager.Domain;
using TaskManager.Infrastructure;

string dataFile = Environment.GetEnvironmentVariable("TASK_DATA_FILE")
    ?? Path.Combine(AppContext.BaseDirectory, "tasks.json");

try
{
    var repository = new JsonTodoRepository(dataFile);
    var service = new TodoService(repository);
    RunCommand(args, service);
}
catch (ArgumentException exception)
{
    Console.Error.WriteLine($"Input không hợp lệ: {exception.Message}");
    Environment.ExitCode = 2;
}
catch (InvalidDataException exception)
{
    Console.Error.WriteLine(exception.Message);
    Environment.ExitCode = 3;
}
catch (IOException exception)
{
    Console.Error.WriteLine($"Không thể đọc/ghi dữ liệu: {exception.Message}");
    Environment.ExitCode = 4;
}
catch (UnauthorizedAccessException exception)
{
    Console.Error.WriteLine($"Không có quyền đọc/ghi dữ liệu: {exception.Message}");
    Environment.ExitCode = 4;
}

static void RunCommand(string[] arguments, TodoService service)
{
    if (arguments.Length == 0)
    {
        PrintUsage();
        return;
    }

    string command = arguments[0].ToLowerInvariant();

    switch (command)
    {
        case "add":
            RequireArgumentCount(arguments, expected: 2);
            TodoItemView added = service.Add(arguments[1]);
            Console.WriteLine($"Đã thêm #{added.Id}: {added.Title}");
            break;

        case "list":
            RequireArgumentCount(arguments, expected: 1);
            PrintItems(service.GetAll());
            break;

        case "done":
            RequireArgumentCount(arguments, expected: 2);
            int doneId = ParsePositiveId(arguments[1]);
            if (!service.MarkCompleted(doneId))
            {
                Console.Error.WriteLine($"Không tìm thấy công việc #{doneId}.");
                Environment.ExitCode = 1;
            }
            else
            {
                Console.WriteLine($"Đã hoàn thành #{doneId}.");
            }
            break;

        case "remove":
            RequireArgumentCount(arguments, expected: 2);
            int removeId = ParsePositiveId(arguments[1]);
            if (!service.Remove(removeId))
            {
                Console.Error.WriteLine($"Không tìm thấy công việc #{removeId}.");
                Environment.ExitCode = 1;
            }
            else
            {
                Console.WriteLine($"Đã xóa #{removeId}.");
            }
            break;

        default:
            Console.Error.WriteLine($"Lệnh không hỗ trợ: {command}");
            PrintUsage();
            Environment.ExitCode = 2;
            break;
    }
}

static void PrintItems(IReadOnlyList<TodoItemView> items)
{
    if (items.Count == 0)
    {
        Console.WriteLine("Chưa có công việc.");
        return;
    }

    foreach (TodoItemView item in items)
    {
        string marker = item.Status == TodoStatus.Completed ? "x" : " ";
        Console.WriteLine(
            $"[{marker}] #{item.Id} {item.Title} " +
            $"({item.CreatedAt:yyyy-MM-dd HH:mm} UTC)");
    }
}

static int ParsePositiveId(string input)
{
    bool success = int.TryParse(
        input,
        NumberStyles.None,
        CultureInfo.InvariantCulture,
        out int id);

    if (!success || id <= 0)
    {
        throw new ArgumentException("ID phải là số nguyên dương.", nameof(input));
    }

    return id;
}

static void RequireArgumentCount(string[] arguments, int expected)
{
    if (arguments.Length != expected)
    {
        throw new ArgumentException(
            $"Lệnh cần {expected - 1} đối số nhưng nhận " +
            $"{arguments.Length - 1}.");
    }
}

static void PrintUsage()
{
    Console.WriteLine("Cách dùng:");
    Console.WriteLine("  dotnet run -- add \"Hoc C#\"");
    Console.WriteLine("  dotnet run -- list");
    Console.WriteLine("  dotnet run -- done <id>");
    Console.WriteLine("  dotnet run -- remove <id>");
}
```

### 3.6 Build và chạy end-to-end

```bash
dotnet build --configuration Release

# Dùng một đường dẫn rõ ràng để biết JSON nằm ở đâu.
export TASK_DATA_FILE="$PWD/data/tasks.json"

dotnet run --configuration Release -- add "Hoc C# co ban"
dotnet run --configuration Release -- add "Viet bai tap"
dotnet run --configuration Release -- list
dotnet run --configuration Release -- done 1
dotnet run --configuration Release -- remove 2
dotnet run --configuration Release -- list
```

Kết quả có cùng cấu trúc sau; timestamp sẽ khác:

```text
Đã thêm #1: Hoc C# co ban
Đã thêm #2: Viet bai tap
[ ] #1 Hoc C# co ban (2026-07-30 08:30 UTC)
[ ] #2 Viet bai tap (2026-07-30 08:31 UTC)
Đã hoàn thành #1.
Đã xóa #2.
[x] #1 Hoc C# co ban (2026-07-30 08:30 UTC)
```

## 4. Giải thích cơ chế

### 4.1 Luồng thực thi một lệnh `add`

```text
shell
  │ truyền string[] args
  ▼
Program.cs
  │ tạo JsonTodoRepository và TodoService
  ▼
TodoService.Add(title)
  │ kiểm tra ID, tạo TodoItem, thêm vào List
  ▼
ITodoRepository.Save(items)
  │ map domain object -> TodoDocument -> JSON
  ▼
tasks.json.tmp ── File.Move(overwrite) ──> tasks.json
```

`Program.cs` chỉ chịu trách nhiệm chuyển input/output. `TodoService` quyết định thao tác nghiệp vụ. `JsonTodoRepository` biết cách biến dữ liệu thành JSON. `TodoItem` tự bảo vệ trạng thái hợp lệ.

### 4.2 Vì sao dùng DTO riêng cho JSON?

Nếu cho serializer sửa thẳng mọi property của `TodoItem`, code lưu trữ có thể tạo domain object không qua validation. `TodoDocument` có setter công khai vì nhiệm vụ của nó là vận chuyển dữ liệu. Khi load, repository gọi constructor `TodoItem`; invariant được kiểm tra lại tại biên vào.

### 4.3 Ghi file tạm giải quyết được gì?

`Save` serialize toàn bộ state thành string rồi ghi `tasks.json.tmp`. Chỉ khi ghi xong, `File.Move(..., overwrite: true)` mới thay file chính. Nếu serialize hoặc ghi file tạm thất bại, file chính cũ chưa bị đụng tới.

### 4.4 Exit code

- `0`: lệnh chạy thành công hoặc chỉ in hướng dẫn.
- `1`: input đúng dạng nhưng không tìm thấy công việc.
- `2`: sai command hoặc argument.
- `3`: JSON đã hỏng.
- `4`: lỗi I/O.

Shell và pipeline có thể dựa vào exit code thay vì phải đọc câu tiếng Việt trên màn hình.

## 5. Kiến thức nền

### 5.1 Invariant nằm trong domain object

`TodoItem` không cho code ngoài gán `Status` hoặc `Title` tùy ý. Thay đổi phải đi qua `Rename` và `MarkCompleted`. Constructor kiểm tra ID/title nên object vừa tạo đã hợp lệ.

### 5.2 Interface là hợp đồng, class là implementation

`TodoService` chỉ biết `ITodoRepository`. Hiện tại object thật là `JsonTodoRepository`; về sau có thể thay bằng database repository mà không đổi rule `Add`, `MarkCompleted` và `Remove`.

Đây là lợi ích trực tiếp của interface, không phải lý do để tạo interface cho mọi class. Ranh giới lưu trữ có khả năng thay đổi nên abstraction này có mục đích rõ.

### 5.3 Collection và quyền sửa

Service giữ `List<TodoItem>` vì cần `Add` và `Remove`, nhưng không trả list hay mutable item ra ngoài. `GetAll` tạo các `TodoItemView` chỉ đọc rồi bọc list kết quả; caller không thể gọi `Rename`/`MarkCompleted` trên domain object mà quên `Save`. Đây là snapshot nông an toàn vì các field value được copy và `string` là immutable. Đổi lại, mỗi lần gọi tạo allocation; hệ thống lớn có thể dùng projection/read model tối ưu hơn sau khi đo.

`readonly` ở field `_items` chỉ ngăn gán field sang list khác sau constructor; nó không làm nội dung list bất biến. Quyền mutation đến từ việc service giữ kín reference mutable và chỉ công khai operation có kiểm soát.

### 5.4 UTC và thời gian hiển thị

Project lưu `DateTimeOffset.UtcNow`, vì một mốc thời gian cần offset rõ ràng. UI đang hiển thị UTC. Ứng dụng thực tế có thể chuyển sang timezone của người dùng ở biên hiển thị, nhưng dữ liệu lưu vẫn nên có offset hoặc UTC nhất quán.

### Đào sâu (có thể quay lại sau)

#### Mỗi lần `new` tạo gì?

Sau hai dòng trong `Program.cs`:

```csharp
var repository = new JsonTodoRepository(dataFile);
var service = new TodoService(repository);
```

mô hình logic là:

```text
Biến/reference đang dùng              Managed heap
────────────────────────              ────────────
repository ─────────────────────────> JsonTodoRepository object A
                                      └─ _filePath ───────> string object

service ────────────────────────────> TodoService object B
                                      ├─ _repository ─────> object A
                                      └─ _items ──────────> List<TodoItem> object C
                                                             └─ internal array D
```

Hai lần `new` ở đây tạo hai object riêng: A và B. Constructor của `TodoService` gọi `Load`, nên còn có object `List<TodoItem>` C và mảng nội bộ D. Field `_repository` không sao chép repository; nó giữ thêm một reference đến chính object A.

Khi `Add` chạy:

```text
local item ───────────────┐
                         ▼
                      TodoItem object E
                         ▲
List internal array[index]┘
```

Local variable `item` và một phần tử trong `List<TodoItem>` cùng tham chiếu object E. Sau khi method kết thúc, local `item` không còn dùng, nhưng E vẫn reachable qua list nên chưa đủ điều kiện để GC thu hồi.

Các field `Id` (`int`), `Status` (`enum`) và `CreatedAt` (`DateTimeOffset`, một `struct`) là value data nằm inline trong object E. Field `Title` giữ reference đến một string object; nó không chứa trực tiếp toàn bộ ký tự theo mô hình field reference.

Cách này giảm nguy cơ file chính bị ghi dở, nhưng chưa phải transaction bền vững cho mọi filesystem và mọi kiểu sự cố. Hệ thống nhiều process còn cần lock hoặc database. Bài này chỉ có một process thao tác tại một thời điểm.

#### Độ phức tạp hiện tại

`FindById` và `GetNextId` duyệt list nên có thời gian tuyến tính theo số công việc. Với dữ liệu cá nhân nhỏ, lựa chọn này đơn giản và đủ tốt. Khi dữ liệu lớn, database/index hoặc `Dictionary<int, TodoItem>` có thể phù hợp hơn; không tối ưu trước khi có nhu cầu.

## 6. Lỗi thường gặp

### Để mọi property có public setter

```csharp
item.Id = -10;
item.Title = "";
```

Code ngoài có thể phá invariant. Hãy giữ setter `private` hoặc chỉ cung cấp method diễn tả hành động hợp lệ.

### Trả thẳng `List<TodoItem>` từ service

Caller có thể gọi `Clear()` mà repository không được lưu. Chỉ đổi static type thành `IReadOnlyList<T>` cũng chưa đủ nếu caller downcast được backing list, và element class vẫn có thể mutable. Hãy trả wrapper/snapshot/read model không làm lộ collection hoặc domain object cần bảo vệ.

### Nối argument thành title mà không quy định cú pháp

Chương trình yêu cầu title là một argument, vì vậy title có khoảng trắng phải đặt trong dấu nháy ở shell. Nếu muốn nhận mọi argument còn lại, hãy quy định rõ rồi nối chúng có chủ đích.

### Bắt `Exception` rồi coi như thành công

Nuốt mọi lỗi làm mất nguyên nhân và trả exit code sai. Chỉ bắt lỗi mà boundary hiện tại biết cách chuyển thành thông báo; để lỗi lập trình bất ngờ lộ ra trong lúc phát triển.

### Cho rằng file JSON an toàn với nhiều process

Hai process có thể cùng load state cũ rồi lần lượt ghi đè, làm mất cập nhật. File repository hiện có giả định single-process. Muốn concurrent writers cần cơ chế khóa, optimistic concurrency hoặc database.

### Tìm file ở sai nơi

Nếu không đặt `TASK_DATA_FILE`, code dùng `AppContext.BaseDirectory`, thường là thư mục output chứ không phải current directory. Khi phát triển, hãy set biến môi trường như lệnh mẫu để vị trí dữ liệu rõ ràng.

### Dùng `int.Parse` cho input người dùng

`int.Parse` ném exception với input thường xuyên có thể sai. `TryParse` biểu diễn đúng nhánh “hợp lệ/không hợp lệ”, sau đó code chủ động tạo thông báo phù hợp.

## 7. Bài tập

### Bài 1 — Lệnh `rename`

Thêm cú pháp `rename <id> "title mới"`, gọi `TodoItem.Rename` và chỉ lưu khi ID tồn tại.

**Gợi ý:** thêm method `Rename(int id, string title)` vào `TodoService`; tái sử dụng `FindById`.

### Bài 2 — Lọc theo trạng thái

Hỗ trợ `list pending`, `list completed` và `list all`.

**Gợi ý:** parse argument tại UI; service có thể trả một list mới chứa đúng item. Chưa cần LINQ.

### Bài 3 — Ngày đến hạn

Thêm `DueAt` có thể rỗng, validate ngày đến hạn và hiển thị công việc quá hạn.

**Gợi ý:** dùng `DateTimeOffset?`; phân biệt “không có hạn” với `DateTimeOffset.MinValue`.

### Bài 4 — Không làm mất file backup

Trước khi thay file chính, tạo `tasks.json.bak`; thêm lệnh `restore` để phục hồi.

**Gợi ý:** xác định rõ thứ tự copy, ghi tạm và move. Cố tình làm hỏng JSON để kiểm tra luồng phục hồi.

### Bài 5 — Tách thành nhiều project

Tạo solution gồm `TaskManager.Domain`, `TaskManager.Application`, `TaskManager.Infrastructure` và `TaskManager.Console`, rồi đặt project reference đúng chiều.

**Gợi ý:** Domain không reference project nào; Application reference Domain; Infrastructure reference Application và Domain; Console ghép các implementation.

## 8. Checklist tự đánh giá và điều hướng

### Checklist

- [ ] Tôi build được project với `dotnet build --configuration Release` mà không có warning.
- [ ] Tôi chạy được chuỗi `add → list → done → remove` trên một file dữ liệu mới.
- [ ] Tôi chỉ ra được trách nhiệm của `Program`, `TodoService`, `TodoItem` và `JsonTodoRepository`.
- [ ] Tôi vẽ được object graph sau khi tạo repository, service và hai công việc.
- [ ] Tôi giải thích được vì sao hai reference có thể cùng trỏ một `TodoItem`.
- [ ] Tôi phân biệt `readonly` field với immutable object.
- [ ] Tôi mô tả được giới hạn single-process và failure mode của JSON repository.
- [ ] Tôi làm được ít nhất ba bài tập mà không xem lời giải đầy đủ.

### Điều hướng

- Bài prerequisite: [Debug và diagnostics cơ bản](./15-debug-va-diagnostics-co-ban.md).
- Ôn lại trọng tâm memory: [Stack, heap, value type và reference type](./05-stack-heap-value-type-reference-type.md).
- Theo dõi bài tiếp theo trong roadmap: [Module 05 — C# nâng cao](../PROGRESS.md#05-csharp-nang-cao).

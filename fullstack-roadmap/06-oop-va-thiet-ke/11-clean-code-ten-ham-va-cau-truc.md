# Clean code: tên, hàm và cấu trúc

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- Clean code làm ý định rõ qua tên, mức trừu tượng và dữ liệu có cấu trúc.
- Dùng guard clause và tách format khỏi quyết định khi giảm công đọc có thể chỉ ra.
- Bốn output khớp không chứng minh mọi đầu vào tương đương.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đặt tên biến, hàm, class và hằng số nói đúng ý định thay vì mô tả kiểu dữ liệu;
- viết hàm ở một mức trừu tượng, dùng guard clause để bỏ lồng ghép sâu;
- thay magic number bằng hằng số có tên và thay cờ `bool` bằng thiết kế rõ nghĩa;
- tách quyết định khỏi trình bày để mỗi phần kiểm thử được riêng;
- áp dụng command–query separation ở mức method;
- viết comment giải thích **tại sao**, và biết khi nào comment là dấu hiệu tên chưa tốt;
- kiểm chứng rằng một lần dọn code không làm đổi hành vi.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một phiếu ghi “P:120” buộc người sau đoán ý nghĩa và cắt chuỗi. Trả hạng và điểm riêng giúp người hiển thị chọn câu chữ mà không đụng quy tắc tính điểm.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| guard clause | kiểm trường hợp đặc biệt rồi thoát | null/không chi tiêu |
| query | trả dữ liệu không đổi state quan sát | Evaluate |
| command | thao tác có chủ đích đổi state | Save ở bài trước |
| characterization | ghi hành vi hiện tại để đối chiếu | legacy/clean outputs |

### Ví dụ nhỏ — tính tay trước

4999999 →Silver49;5000000 →Gold50;10000000 →Platinum100. DoublePoints nhân điểm, không thay ngưỡng hạng.

Hệ thống có method xếp hạng khách hàng thân thiết, viết cách đây vài năm:

```csharp
public string Do(Cust c, bool f)
{
    string r = "";
    if (c != null)
    {
        if (c.T > 0)
        {
            if (c.T >= 10000000) { r = "P"; }
            else if (c.T >= 5000000) { r = "G"; }
            else { r = "S"; }

            int p = (int)(c.T / 100000);
            if (f) { p = p * 2; }
            r = r + ":" + p;
        }
        else { r = "N:0"; }
    }

    return r;
}
```

Method này chạy đúng. Vấn đề là mọi câu hỏi về nó đều tốn thời gian:

- `f` là gì? Phải đi tìm caller mới biết đó là “đang có chương trình nhân đôi điểm”.
- `10000000` từ đâu ra? Không ai dám sửa vì không biết còn chỗ nào dùng con số đó.
- Chuỗi `"P:100"` là dữ liệu hay là định dạng hiển thị? Nếu bộ phận khác cần cùng dữ liệu ở dạng khác thì phải cắt chuỗi.
- Muốn kiểm tra riêng công thức tính điểm cũng không được, vì nó dính liền với việc dựng chuỗi.

Clean code không phải chuyện thẩm mỹ. Mỗi vấn đề trên đều biến thành thời gian đọc, thời gian dò lỗi và rủi ro sửa nhầm. Bài này dọn đúng method đó và **chứng minh hành vi không đổi**.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir CleanCodeDemo
cd CleanCodeDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `CleanCodeDemo.csproj` bằng:

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

Chương trình giữ **cả hai** phiên bản và so sánh output của chúng trên cùng bộ dữ liệu. Đây là cách rẻ nhất để chắc chắn việc dọn code không đổi hành vi.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;
using System.Globalization;

namespace CleanCodeDemo;

// ============ Bản cũ, giữ nguyên để đối chiếu ============

public sealed class Cust
{
    public Cust(string i, decimal t)
    {
        I = i;
        T = t;
    }

    public string I { get; }

    public decimal T { get; }
}

public sealed class LegacyCalculator
{
    public string Do(Cust? c, bool f)
    {
        string r = string.Empty;
        if (c != null)
        {
            if (c.T > 0)
            {
                if (c.T >= 10000000) { r = "P"; }
                else if (c.T >= 5000000) { r = "G"; }
                else { r = "S"; }

                int p = (int)(c.T / 100000);
                if (f) { p = p * 2; }
                r = r + ":" + p;
            }
            else { r = "N:0"; }
        }

        return r;
    }
}

// ============ Bản đã dọn ============

public enum LoyaltyTier
{
    None = 0,
    Silver = 1,
    Gold = 2,
    Platinum = 3
}

public enum PointsCampaign
{
    Standard = 0,
    DoublePoints = 1
}

public sealed record CustomerSpending(string CustomerId, decimal TotalSpent)
{
    public bool HasSpentAnything => TotalSpent > 0m;
}

public sealed record LoyaltyStatus(LoyaltyTier Tier, int Points);

public sealed class LoyaltyPolicy
{
    private const decimal PlatinumThreshold = 10_000_000m;
    private const decimal GoldThreshold = 5_000_000m;
    private const decimal SpendingPerPoint = 100_000m;
    private const int DoublePointsMultiplier = 2;

    // Query: chỉ trả kết quả, không đổi state, không in ra gì.
    public LoyaltyStatus Evaluate(CustomerSpending spending, PointsCampaign campaign)
    {
        ArgumentNullException.ThrowIfNull(spending);

        if (!spending.HasSpentAnything)
        {
            return new LoyaltyStatus(LoyaltyTier.None, 0);
        }

        LoyaltyTier tier = DetermineTier(spending.TotalSpent);
        int points = CalculatePoints(spending.TotalSpent, campaign);
        return new LoyaltyStatus(tier, points);
    }

    private static LoyaltyTier DetermineTier(decimal totalSpent) => totalSpent switch
    {
        >= PlatinumThreshold => LoyaltyTier.Platinum,
        >= GoldThreshold => LoyaltyTier.Gold,
        _ => LoyaltyTier.Silver
    };

    private static int CalculatePoints(decimal totalSpent, PointsCampaign campaign)
    {
        int basePoints = (int)(totalSpent / SpendingPerPoint);
        return campaign == PointsCampaign.DoublePoints
            ? basePoints * DoublePointsMultiplier
            : basePoints;
    }
}

// Trình bày tách khỏi quyết định: đổi định dạng không đụng tới quy tắc.
public static class LoyaltyStatusFormatter
{
    public static string ToCompactCode(LoyaltyStatus status)
    {
        ArgumentNullException.ThrowIfNull(status);

        string tierCode = status.Tier switch
        {
            LoyaltyTier.Platinum => "P",
            LoyaltyTier.Gold => "G",
            LoyaltyTier.Silver => "S",
            LoyaltyTier.None => "N",
            _ => throw new ArgumentOutOfRangeException(nameof(status), status.Tier, "Unknown tier.")
        };

        return $"{tierCode}:{status.Points.ToString(CultureInfo.InvariantCulture)}";
    }

    public static string ToSentence(LoyaltyStatus status)
    {
        ArgumentNullException.ThrowIfNull(status);

        return status.Tier == LoyaltyTier.None
            ? "Chưa phát sinh chi tiêu."
            : $"Hạng {status.Tier}, {status.Points} điểm.";
    }
}

internal static class Program
{
    private static void Main()
    {
        var samples = new List<(string CustomerId, decimal TotalSpent, PointsCampaign Campaign)>
        {
            ("CUS-001", 12_000_000m, PointsCampaign.Standard),
            ("CUS-002", 6_500_000m, PointsCampaign.DoublePoints),
            ("CUS-003", 900_000m, PointsCampaign.Standard),
            ("CUS-004", 0m, PointsCampaign.DoublePoints)
        };

        var legacy = new LegacyCalculator();
        var policy = new LoyaltyPolicy();
        bool allMatch = true;

        foreach ((string customerId, decimal totalSpent, PointsCampaign campaign) in samples)
        {
            string legacyOutput = legacy.Do(
                new Cust(customerId, totalSpent),
                campaign == PointsCampaign.DoublePoints);

            LoyaltyStatus status = policy.Evaluate(
                new CustomerSpending(customerId, totalSpent),
                campaign);

            string cleanOutput = LoyaltyStatusFormatter.ToCompactCode(status);
            bool matches = string.Equals(legacyOutput, cleanOutput, StringComparison.Ordinal);
            allMatch &= matches;

            Console.WriteLine(
                $"{customerId}: legacy={legacyOutput}, clean={cleanOutput}, match={matches}");
            Console.WriteLine($"          {LoyaltyStatusFormatter.ToSentence(status)}");
        }

        Console.WriteLine($"Behaviour preserved: {allMatch}");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
CUS-001: legacy=P:120, clean=P:120, match=True
          Hạng Platinum, 120 điểm.
CUS-002: legacy=G:130, clean=G:130, match=True
          Hạng Gold, 130 điểm.
CUS-003: legacy=S:9, clean=S:9, match=True
          Hạng Silver, 9 điểm.
CUS-004: legacy=N:0, clean=N:0, match=True
          Chưa phát sinh chi tiêu.
Behaviour preserved: True
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Legacy trộn tính và format; bản mới Evaluate trả LoyaltyStatus.
2. Guard chặn null, chi tiêu<=0 trả None0 trước tính tier.
3. Formatter ánh xạ enum sang mã/câu; không sửa policy state.
4. Policy không giữ mutable state; O(1) arithmetic và allocation record/string mỗi call. Int điểm có giới hạn, không dùng test nhỏ để hứa an toàn mọi decimal.

### Mini-check

Test ngay dưới/đúng/trên ngưỡng hạng bắt được lỗi nào mà bốn sample giữa khoảng không bắt?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Tên nói ý định, không nói kiểu dữ liệu

| Bản cũ | Bản mới | Vì sao |
|---|---|---|
| `Do` | `Evaluate` | động từ nói việc gì đang xảy ra |
| `c` | `spending` | vai trò của tham số, không phải chữ cái đầu của type |
| `T` | `TotalSpent` | đơn vị và ý nghĩa rõ ràng |
| `f` | `campaign` | và kiểu đổi từ `bool` sang `enum` |
| `r` | giá trị trả về có kiểu `LoyaltyStatus` | không cần biến tích lũy |
| `10000000` | `PlatinumThreshold` | tìm kiếm được, sửa một chỗ |

Quy ước dùng trong sample và trong cả bộ tài liệu này: class là danh từ, method là cụm động từ, property là danh từ, biểu thức `bool` đọc như một khẳng định (`HasSpentAnything`).

### Guard clause phá lồng ghép

Bản cũ lồng ba tầng `if`. Bản mới xử lý trường hợp đặc biệt trước rồi thoát:

```csharp
if (!spending.HasSpentAnything)
{
    return new LoyaltyStatus(LoyaltyTier.None, 0);
}
```

Sau dòng đó, phần còn lại của method chỉ nói về “đường chính”. Kiểm tra `null` cũng biến mất khỏi thân method vì `ArgumentNullException.ThrowIfNull` xử lý ngay đầu — cách đã dùng xuyên suốt module 05.

### Một hàm, một mức trừu tượng

`Evaluate` đọc như mô tả nghiệp vụ: kiểm tra chi tiêu, xác định hạng, tính điểm, trả kết quả. Nó **không** chứa ngưỡng, không chứa phép chia, không chứa chuỗi. Chi tiết nằm ở hai method private một dòng ý.

Đây là tiêu chí thực dụng hơn “hàm phải dưới 20 dòng”: nếu trong một hàm có cả câu chuyện nghiệp vụ lẫn phép toán chi tiết, người đọc phải liên tục đổi độ cao khi đọc.

### Tách quyết định khỏi trình bày

`LoyaltyPolicy` trả `LoyaltyStatus` — dữ liệu. `LoyaltyStatusFormatter` biến dữ liệu thành chuỗi. Nhờ đó có hai cách hiển thị (`ToCompactCode`, `ToSentence`) trên cùng một kết quả, và thêm cách thứ ba không đụng tới quy tắc.

Bản cũ trả `"P:120"` nên bộ phận cần con số phải cắt chuỗi — một dạng phụ thuộc vào định dạng mà không ai khai báo.

### Kiểm chứng hành vi không đổi

Vòng lặp trong `Main` chạy cả hai phiên bản trên cùng dữ liệu và so sánh từng kết quả. Dòng `Behaviour preserved: True` là bằng chứng cho bốn ca đã chạy, không chứng minh tương đương trên mọi input. Bản cũ nhận null và trả chuỗi rỗng; API mới từ chối null. Với số điểm rất lớn, phép nhân int vẫn có thể overflow như bản cũ; cần đặt miền chi tiêu trước khi tuyên bố tương đương.

Đây chính là ý tưởng của **characterization test**: chốt hành vi hiện tại trước, rồi mới dọn. [Bài 12](./12-code-smell-va-refactoring.md) sẽ dùng lại kỹ thuật này một cách hệ thống, và [module 14](../PROGRESS.md#14-testing-chat-luong) sẽ thay `Main` bằng test framework thật.

### Đào sâu (có thể quay lại sau)

#### Command–query separation

Chia method thành hai loại:

- **Query**: trả dữ liệu, không đổi state quan sát được. `Evaluate`, `DetermineTier`.
- **Command**: đổi state, thường trả `void` hoặc một kết quả trạng thái. `Save`, `Place`.

Một method vừa trả giá trị vừa âm thầm đổi state là nguồn bug khó thấy, vì người đọc tưởng gọi nó là an toàn. Quy tắc này không tuyệt đối — `TryAdd` vừa đổi state vừa trả `bool` và vẫn hợp lý — nhưng khi phá luật, tên method phải nói rõ.

#### Số lượng tham số

Ba tham số trở lên bắt đầu khó nhớ thứ tự. Cách xử lý theo thứ tự ưu tiên: gom các tham số luôn đi cùng nhau thành một record (như `CustomerSpending`); tách method nếu chúng phục vụ hai việc; dùng named arguments ở call site như đã học ở [module 04, bài 4](../04-csharp-co-ban/04-method-parameter-va-return.md).

#### Comment nào đáng giữ

Giữ comment trả lời **tại sao**: vì sao ngưỡng là `10.000.000`, vì sao phải làm tròn xuống, vì sao có ngoại lệ cho một đối tác. Bỏ comment mô tả **cái gì** khi code đã tự nói. Bỏ hẳn code bị comment lại — Git đã giữ lịch sử rồi.

Với API công khai của thư viện, XML doc (`/// <summary>`) lại có giá trị riêng vì nó hiện trong IntelliSense của người dùng thư viện.

#### Định dạng và công cụ

Đừng tranh luận thủ công về dấu cách và thứ tự `using`. Dùng `.editorconfig` cùng `dotnet format`, và bật cảnh báo compiler thành lỗi như mọi project trong bộ tài liệu này. Phần cấu hình đầy đủ nằm ở [module 14](../PROGRESS.md#14-testing-chat-luong).

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| chuỗi làm kết quả nghiệp vụ | phải parse lại để dùng số | khó đổi presentation |
| record kết quả + formatter | tách data và display | thêm type có ý nghĩa |
| tách mọi biểu thức | nhiều method một dòng | không dùng nếu tên không thêm thông tin |

### Misconception check

**Đúng hay sai?** Guard clause luôn giữ hành vi của null như trước.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: legacy trả rỗng, bản mới ném; đây là thay đổi contract.

</details>

**Đúng hay sai?** Behaviour preserved True là chứng minh toán học.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ chứng nhận ca đã đối chiếu.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** tên và guard.

- **Working Developer — dùng khi làm việc:** oracle và miền tương đương.

- **Deep Dive — có thể quay lại sau:** culture/overflow ngoài miền.

### Bộ quy tắc đặt tên dùng được ngay

| Loại | Quy ước | Ví dụ tốt | Ví dụ nên tránh |
|---|---|---|---|
| Class | danh từ, `PascalCase` | `LoyaltyPolicy` | `LoyaltyManager`, `Helper` |
| Method | cụm động từ | `CalculatePoints` | `Process`, `Do`, `Handle2` |
| Boolean | khẳng định đọc được | `HasSpentAnything`, `IsExpired` | `flag`, `status`, `check` |
| Hằng số | ý nghĩa nghiệp vụ | `GoldThreshold` | `MAGIC_5000000` |
| Interface | vai trò | `IOrderReader` | `IOrderInterface` |
| Biến cục bộ | vai trò trong ngữ cảnh | `basePoints` | `tmp`, `data`, `x1` |

Hai quy tắc bổ sung: dùng **một** từ cho **một** khái niệm trong toàn hệ thống (đã chọn `Find` thì đừng chỗ khác dùng `Fetch`), và đừng viết tắt trừ khi từ viết tắt phổ biến hơn từ đầy đủ (`Id`, `Url`, `Sku`).

### Dấu hiệu một hàm cần tách

- Có comment kiểu `// bước 2: ...` chia thân hàm thành các đoạn.
- Có hơn hai tầng lồng ghép.
- Có biến tích lũy được dùng lại cho nhiều mục đích khác nhau.
- Tên hàm phải dùng chữ “và” mới mô tả đủ.
- Phải cuộn màn hình mới đọc hết.

### Cấu trúc file dễ đọc

Thứ tự thường dùng trong C#: hằng số, field, constructor, property, method công khai, method private. Người đọc gặp phần công khai trước — tức là gặp “hàm ý của class” trước chi tiết. Đây cũng là thứ tự dùng trong mọi sample của module này.

### Clean code và các nguyên tắc thiết kế

Clean code làm việc ở mức nhỏ nhất: tên, hàm, file. Nó không thay được thiết kế. Một hệ thống có tên đẹp nhưng chiều phụ thuộc sai vẫn khó bảo trì. Ngược lại, thiết kế đúng mà tên tối nghĩa thì không ai đọc nổi để tận dụng thiết kế đó. Hai mức bổ sung cho nhau.

## 6. Lỗi thường gặp

### Đổi tên kèm sửa logic trong cùng một commit

Khi có lỗi, không ai biết nó đến từ việc dọn hay từ thay đổi hành vi. Hãy tách thành hai commit: một commit chỉ đổi tên/cấu trúc, một commit đổi hành vi.

### Tên dài dòng thay vì chính xác

`CalculateTheTotalNumberOfLoyaltyPointsForTheCustomer` không rõ hơn `CalculatePoints` trong ngữ cảnh của `LoyaltyPolicy`. Ngữ cảnh của class đã mang một phần thông tin; đừng lặp lại nó trong tên method.

### Viết comment thay vì sửa tên

```csharp
// t là tổng chi tiêu trong 12 tháng
decimal t;
```

Comment này sẽ lạc hậu. Đổi tên thành `spentLast12Months` là xong.

### Giữ magic number vì “ai cũng biết”

Sáu tháng sau, chính bạn cũng không nhớ `0.08m` là VAT hay phí dịch vụ. Đặt tên cho nó, và nếu giá trị đến từ nghiệp vụ thì cân nhắc đưa vào cấu hình như `ShippingRates` ở [bài 9](./09-coupling-va-cohesion.md).

### Tách hàm quá vụn

Method một dòng chỉ để đặt tên cho một biểu thức đơn giản làm người đọc phải nhảy liên tục. Tách khi đoạn code có một khái niệm đáng đặt tên, không tách theo số dòng.

### Trả về chuỗi đã định dạng từ lớp nghiệp vụ

Đây là lỗi của bản cũ. Chuỗi hiển thị là quyết định của tầng trình bày; lớp nghiệp vụ nên trả dữ liệu có cấu trúc.

### “Dọn” bằng cách viết lại từ đầu

Viết lại một module cũ mà không có cách kiểm chứng hành vi là cách chắc chắn nhất để đánh mất các trường hợp đặc biệt đã được xử lý qua nhiều năm. Hãy chốt hành vi trước, dọn từng bước sau.

## 7. Khi nào KHÔNG dùng

Không rename và đổi business rule trong cùng bước khó review. Không áp số dòng hàm cứng; tách khi có khái niệm và mức trừu tượng cần đặt tên.

## 8. Production notes & scale check

Verifier đối chiếu1000ca seed cố định và các biên trong miền không tràn điểm; kiểm null contract riêng. Bản cũ/ mới dùng culture khác trong một số format; gate chạy culture đã nêu và không hứa tương đương mọi locale.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Đặt lại tên

Cho `void P(List<string> l, int n, bool b)` xử lý danh sách SKU. Đặt lại tên cho method và mọi tham số dựa trên một mô tả nghiệp vụ do bạn tự chọn.

**Gợi ý:** viết một câu tiếng Việt mô tả method trước, rồi rút tên từ chính câu đó.

### Bài 2 — Guard clause

Viết lại một method có ba tầng `if` lồng nhau trong code của bạn thành dạng thoát sớm, giữ nguyên hành vi.

**Gợi ý:** đảo điều kiện của tầng ngoài cùng trước; chạy lại test đối chiếu sau mỗi bước.

### Bài 3 — Hằng số có tên

Tìm ba magic number trong sample của các bài trước và đặt tên cho chúng. Giải thích cái nào nên là hằng số, cái nào nên là cấu hình truyền vào.

**Gợi ý:** hỏi “giá trị này có khác nhau giữa các môi trường hay giữa các khách hàng không?”.

### Bài 4 — Thêm định dạng thứ ba

Thêm `ToJson(LoyaltyStatus)` vào formatter mà không sửa `LoyaltyPolicy`. Kiểm tra `Behaviour preserved` vẫn `True`.

**Gợi ý:** dựng chuỗi bằng `StringBuilder` hoặc nội suy; System.Text.Json đã học ở [module 05, bài 17](../05-csharp-nang-cao/17-serialization-system-text-json.md) nếu bạn muốn dùng bản chuẩn.

### Bài 5 — Đối chiếu ngẫu nhiên

Sinh 1.000 giá trị chi tiêu ngẫu nhiên có seed cố định, chạy cả hai phiên bản và khẳng định kết quả trùng khớp toàn bộ.

**Gợi ý:** `new Random(12345)` cho kết quả lặp lại; in ra trường hợp đầu tiên khác nhau nếu có.

## 10. Bài tập tích hợp liên module — Judgment

So policy pure ở SRP với delegate predicate Module05: effect nào khiến “query” khó cache? Dọn tên một method thực tế, nêu cách kiểm chứng behavior trước khi sửa.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. DoublePoints đổi tier không?
2. Null xử lý giống nhau không?
3. Kết quả policy giữ gì ngoài string?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi đặt tên theo ý định và theo từ vựng nghiệp vụ.
- [ ] Tôi dùng guard clause thay cho lồng ghép sâu.
- [ ] Tôi giữ mỗi hàm ở một mức trừu tượng.
- [ ] Tôi thay magic number bằng hằng số có tên và cờ `bool` bằng `enum`.
- [ ] Tôi tách quyết định khỏi trình bày.
- [ ] Tôi kiểm chứng hành vi không đổi trước và sau khi dọn.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Dependency injection và inversion of control](./10-dependency-injection-va-inversion-of-control.md)
- Ôn lại nền tảng: [Method, parameter và return](../04-csharp-co-ban/04-method-parameter-va-return.md), [Pattern matching](../05-csharp-nang-cao/08-pattern-matching.md)
- Bài tiếp theo: [Code smell và refactoring](./12-code-smell-va-refactoring.md)

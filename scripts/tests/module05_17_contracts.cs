using JsonContractDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var contract=AppJsonContext.Default.OrderDto;const string valid="{\"id\":\"A\",\"total\":1,\"status\":\"Paid\",\"createdAt\":\"2026-01-01T00:00:00Z\"}";
var value=System.Text.Json.JsonSerializer.Deserialize(valid,contract)!;Check(value.Id=="A"&&value.Note is null,"roundtrip");foreach(var bad in new[]{valid.Replace("\"total\":1,",""),valid.Replace("\"Paid\"","1"),valid.Replace("\"Paid\"","\"Unknown\""),valid.Replace("\"id\"","\"typo\"")})Throws<System.Text.Json.JsonException>(()=>System.Text.Json.JsonSerializer.Deserialize(bad,contract));
Check(System.Text.Json.JsonSerializer.Deserialize("null",contract) is null,"null representation");var validate=typeof(JsonContractDemo.Program).GetMethod("Validate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static)!;
try{validate.Invoke(null,[value with{Total=-1}]);throw new Exception("expected domain failure");}catch(System.Reflection.TargetInvocationException e){Check(e.InnerException is InvalidOperationException,"domain failure cause");}
}
}

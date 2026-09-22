using DebugDiagnosticsDemo;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var service=new InvoiceService();var items=new[]{new InvoiceItem("A",2,750000m),new InvoiceItem("B",1,350000m)};
Check(service.CalculateTotal("B",items,0.1m)==1665000m,"total");Throws<ArgumentOutOfRangeException>(()=>service.CalculateTotal("B",items,1.1m));
Check(SafeLogValue.MaskEmail("lan@example.com")=="l***@example.com","mask");Throws<ArgumentOutOfRangeException>(()=>new InvoiceItem("X",0,1));
 }
}
